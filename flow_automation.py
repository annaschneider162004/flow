import os
import re
import time
from pathlib import Path
from typing import Callable, Optional

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

import config


class FlowAutomation:
    def __init__(self, log_callback: Optional[Callable] = None):
        self.log_callback = log_callback or print
        self.browser = None
        self.context = None
        self.page = None
        self.download_path = None

    def _log(self, message: str):
        if self.log_callback:
            self.log_callback(message)

    def _ensure_dirs(self):
        Path(config.USER_DATA_DIR).mkdir(parents=True, exist_ok=True)
        Path(config.DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)

    def setup_login(self):
        """Mở trình duyệt để người dùng đăng nhập Google lần đầu"""
        self._ensure_dirs()

        with sync_playwright() as p:
            self.browser = p.chromium.launch_persistent_context(
                user_data_dir=config.USER_DATA_DIR,
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--window-size=1400,900"
                ],
                viewport={"width": 1400, "height": 900},
                accept_downloads=True
            )

            self.page = self.browser.new_page()
            self._log("🌐 Mở trang Flow để bạn đăng nhập...")
            self.page.goto(config.FLOW_URL, wait_until="networkidle")

            self._log("⏳ Vui lòng đăng nhập tài khoản Google có gói Flow Ultra.")
            self._log("   Sau khi đăng nhập xong, bạn có thể đóng trình duyệt.")

            # Chờ người dùng tự đóng
            try:
                while self.page.is_closed() is False:
                    time.sleep(1)
            except Exception:
                pass

            self._log("✅ Đã lưu trạng thái đăng nhập.")

    def generate_video(
        self,
        prompt: str,
        model: str,
        duration: str,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """Tạo video và trả về đường dẫn file đã tải về"""
        self._ensure_dirs()
        
        def update_progress(step: int, total: int, message: str):
            if progress_callback:
                progress_callback(step, total, message)
            self._log(message)

        update_progress(1, 8, "🚀 Khởi động trình duyệt...")

        with sync_playwright() as p:
            self.browser = p.chromium.launch_persistent_context(
                user_data_dir=config.USER_DATA_DIR,
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--window-size=1400,900"
                ],
                viewport={"width": 1400, "height": 900},
                accept_downloads=True,
                downloads_path=os.path.abspath(config.DOWNLOAD_DIR),
            )
            self.page = self.browser.new_page()

            update_progress(2, 8, "🌐 Truy cập Flow.google.com...")
            try:
                self.page.goto(config.FLOW_URL, wait_until="networkidle", timeout=60000)
            except PlaywrightTimeout:
                raise Exception("Không thể truy cập Flow.google.com. Kiểm tra kết nối mạng.")

            # Kiểm tra đã đăng nhập chưa
            if self._is_login_required():
                raise Exception("Chưa đăng nhập. Vui lòng bấm 'Đăng nhập Flow' trước.")

            # Nhập prompt
            update_progress(3, 8, "✍️ Nhập prompt...")
            self._fill_prompt(prompt)

            # Chọn model
            update_progress(4, 8, f"⚙️ Chọn model: {model}...")
            self._select_model(model)

            # Chọn duration
            update_progress(5, 8, f"⏱️ Chọn thời lượng: {duration}...")
            self._select_duration(duration)

            # Click generate
            update_progress(6, 8, "🎬 Đang tạo video (có thể mất vài phút)...")
            self._click_generate()

            # Chờ video xuất hiện
            update_progress(7, 8, "⏳ Chờ video render xong...")
            video_url = self._wait_for_video()

            # Tải video về
            update_progress(8, 8, "💾 Đang tải video về máy...")
            downloaded_path = self._download_video(video_url)

            self.browser.close()
            return downloaded_path

    def _is_login_required(self) -> bool:
        """Phát hiện trang yêu cầu đăng nhập"""
        try:
            if self.page.locator('text="Sign in"').count() > 0:
                return True
            if self.page.locator('text="Đăng nhập"').count() > 0:
                return True
            # Nếu thấy ô prompt => đã đăng nhập
            if self.page.locator(config.SELECTORS["prompt_input"]).count() > 0:
                return False
            return True
        except Exception:
            return True

    def _fill_prompt(self, prompt: str):
        try:
            textarea = self.page.locator(config.SELECTORS["prompt_input"]).first
            textarea.wait_for(state="visible", timeout=10000)
            textarea.fill("")
            textarea.fill(prompt)
            self._log(f"   Prompt: {prompt[:80]}...")
        except Exception as e:
            raise Exception(f"Không tìm thấy ô nhập prompt: {e}")

    def _select_model(self, model: str):
        try:
            dropdown = self.page.locator(config.SELECTORS["model_dropdown"]).first
            
            if dropdown.count() > 0 and dropdown.is_visible():
                dropdown.click()
                self.page.wait_for_timeout(500)
                
                option = self.page.locator(f'text={model}').first
                if option.count() > 0:
                    option.click()
                    self.page.wait_for_timeout(500)
                else:
                    self._log(f"   Không tìm thấy model {model}, bỏ qua.")
            else:
                self._log("   Không tìm thấy dropdown model, bỏ qua.")
        except Exception as e:
            self._log(f"   Lỗi chọn model: {e}")

    def _select_duration(self, duration: str):
        try:
            dropdown = self.page.locator(config.SELECTORS["duration_dropdown"]).first
            
            if dropdown.count() > 0 and dropdown.is_visible():
                dropdown.click()
                self.page.wait_for_timeout(500)
                
                # Tìm option khớp (ví dụ: "12s" hoặc "12 seconds")
                option = self.page.locator(f'text={duration}, text={duration.replace("s", " seconds")}').first
                if option.count() == 0:
                    option = self.page.locator(f'text={duration}').first
                
                if option.count() > 0:
                    option.click()
                    self.page.wait_for_timeout(500)
                else:
                    self._log(f"   Không tìm thấy duration {duration}, bỏ qua.")
            else:
                self._log("   Không tìm thấy dropdown duration, bỏ qua.")
        except Exception as e:
            self._log(f"   Lỗi chọn duration: {e}")

    def _click_generate(self):
        try:
            btn = self.page.locator(config.SELECTORS["generate_button"]).first
            btn.wait_for(state="visible", timeout=10000)
            btn.click()
        except Exception as e:
            # Thử tìm button cuối cùng hoặc theo text khác
            try:
                self.page.get_by_role("button", name=re.compile("generate|create", re.I)).last.click()
            except Exception:
                raise Exception(f"Không tìm thấy nút Generate: {e}")

    def _wait_for_video(self) -> str:
        """Chờ video render xong và lấy URL"""
        max_wait = config.MAX_WAIT_TIME
        interval = 5
        elapsed = 0

        while elapsed < max_wait:
            try:
                # Thử tìm video element
                video_locator = self.page.locator(config.SELECTORS["result_video"]).first
                if video_locator.count() > 0 and video_locator.is_visible():
                    # Lấy src
                    src = video_locator.get_attribute("src") or video_locator.get_attribute("href")
                    if src:
                        self._log(f"   Video URL: {src[:80]}...")
                        return src
            except Exception:
                pass

            # Kiểm tra nếu có lỗi hiển thị
            if self.page.locator('text="error"').count() > 0:
                raise Exception("Flow báo lỗi khi tạo video. Kiểm tra credits hoặc prompt.")

            time.sleep(interval)
            elapsed += interval
            self._log(f"   Đã chờ {elapsed}s...")

        raise Exception(f"Quá thời gian chờ {max_wait}s. Có thể video vẫn đang render hoặc selector đã thay đổi.")

    def _download_video(self, video_url: str) -> str:
        """Tải video từ URL về máy"""
        if video_url.startswith("//"):
            video_url = "https:" + video_url
        elif video_url.startswith("/"):
            video_url = "https://flow.google.com" + video_url

        import requests
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        response = requests.get(video_url, headers=headers, stream=True)
        response.raise_for_status()

        # Xác định tên file
        filename = re.sub(r'[^\w\s-]', '', self.page.title())[:50] or "flow_video"
        filename = f"{filename}_{int(time.time())}.mp4"
        filepath = os.path.join(config.DOWNLOAD_DIR, filename)

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return filepath
