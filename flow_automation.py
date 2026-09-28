import json
import os
import re
import shutil
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
        self._temp_profile_dir = None

    def _log(self, message: str):
        if self.log_callback:
            self.log_callback(message)

    def _ensure_dirs(self):
        Path(config.DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)

    def _get_chrome_args(self) -> list:
        """Trả về args để launch Chrome"""
        return [
            "--disable-blink-features=AutomationControlled",
            "--window-size=1400,900"
        ]

    def _validate_chrome_paths(self):
        """Kiểm tra các đường dẫn Chrome hợp lệ"""
        if not os.path.exists(config.CHROME_EXECUTABLE_PATH):
            raise Exception(
                f"Không tìm thấy Chrome tại:\n{config.CHROME_EXECUTABLE_PATH}\n"
                "Vui lòng sửa CHROME_EXECUTABLE_PATH trong config.py"
            )

        if not os.path.exists(config.CHROME_USER_DATA_DIR):
            raise Exception(
                f"Không tìm thấy thư mục Chrome User Data:\n{config.CHROME_USER_DATA_DIR}\n"
                "Vui lòng sửa CHROME_USER_DATA_DIR trong config.py"
            )

        profile_path = os.path.join(config.CHROME_USER_DATA_DIR, config.CHROME_PROFILE_NAME)
        if not os.path.exists(profile_path):
            raise Exception(
                f"Không tìm thấy profile '{config.CHROME_PROFILE_NAME}' trong:\n{config.CHROME_USER_DATA_DIR}\n"
                "Hãy kiểm tra các profile có sẵn và sửa CHROME_PROFILE_NAME trong config.py"
            )

    def _launch_browser_with_profile(self, playwright):
        """Khởi động Chrome với profile người dùng (dùng cho export cookies)"""
        self._validate_chrome_paths()

        chrome_path = config.CHROME_EXECUTABLE_PATH
        profile_path = os.path.join(config.CHROME_USER_DATA_DIR, config.CHROME_PROFILE_NAME)

        self._log(f"🖥️ Chrome: {chrome_path}")
        self._log(f"👤 Profile: {config.CHROME_PROFILE_NAME} ({profile_path})")

        # Copy profile sang thư mục tạm để tránh xung đột nếu Chrome đang chạy
        self._temp_profile_dir = os.path.abspath(f"./temp_chrome_profile_{int(time.time())}")
        self._log(f"📂 Copy profile tạm: {self._temp_profile_dir}")
        shutil.copytree(profile_path, self._temp_profile_dir, dirs_exist_ok=True)

        browser = playwright.chromium.launch(
            executable_path=chrome_path,
            headless=False,
            args=self._get_chrome_args()
        )

        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            accept_downloads=True
        )

        return browser, context

    def _cleanup_temp_profile(self):
        """Xóa profile tạm sau khi dùng"""
        try:
            if self._temp_profile_dir and os.path.exists(self._temp_profile_dir):
                shutil.rmtree(self._temp_profile_dir, ignore_errors=True)
                self._log(f"🧹 Đã xóa profile tạm: {self._temp_profile_dir}")
        except Exception as e:
            self._log(f"   Không thể xóa profile tạm: {e}")

    def export_cookies_from_chrome(self):
        """Mở Chrome với profile, đợi đăng nhập, rồi lưu storage state"""
        self._ensure_dirs()
        self._log("🌐 Mở Chrome với profile đã cấu hình...")
        self._log("⏳ Vui lòng đăng nhập Flow nếu cần, sau đó đóng trình duyệt.")
        self._log("   Tool sẽ tự động export cookies khi bạn đóng.")

        with sync_playwright() as p:
            try:
                self.browser, self.context = self._launch_browser_with_profile(p)
                self.page = self.context.new_page()
                self.page.goto(config.FLOW_URL, wait_until="networkidle")

                # Chờ người dùng tự đóng trang
                try:
                    while self.page.is_closed() is False:
                        time.sleep(1)
                except Exception:
                    pass

                # Lưu storage state (cookies + localStorage + sessionStorage)
                storage_state = self.context.storage_state(path=config.AUTH_STATE_FILE)
                cookie_count = len(storage_state.get("cookies", []))
                self._log(f"✅ Đã export {cookie_count} cookies vào {config.AUTH_STATE_FILE}")

            finally:
                try:
                    if self.browser:
                        self.browser.close()
                except Exception:
                    pass
                self._cleanup_temp_profile()

    def _load_auth_state(self):
        """Kiểm tra và load cookies/storage state đã export"""
        if not os.path.exists(config.AUTH_STATE_FILE):
            raise Exception(
                f"Không tìm thấy file {config.AUTH_STATE_FILE}\n"
                "Vui lòng bấm 'Export cookies từ Chrome' hoặc 'Import cookies JSON' trước."
            )
        self._log("📂 Đang load cookies đã export...")

    def _launch_browser_with_state(self, playwright):
        """Khởi động Chromium bình thường, load storage state để đăng nhập"""
        self._ensure_dirs()
        self._load_auth_state()

        browser = playwright.chromium.launch(
            headless=False,
            args=self._get_chrome_args()
        )

        context = browser.new_context(
            storage_state=config.AUTH_STATE_FILE,
            viewport={"width": 1400, "height": 900},
            accept_downloads=True
        )

        return browser, context

    def generate_video(
        self,
        prompt: str,
        model: str,
        duration: str,
        image_path: Optional[str] = None,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """Tạo video và trả về đường dẫn file đã tải về"""
        self._ensure_dirs()
        
        def update_progress(step: int, total: int, message: str):
            if progress_callback:
                progress_callback(step, total, message)
            self._log(message)

        update_progress(1, 8, "🚀 Khởi động trình duyệt với cookies...")

        with sync_playwright() as p:
            try:
                self.browser, self.context = self._launch_browser_with_state(p)
                self.page = self.context.new_page()

                update_progress(2, 8, "🌐 Truy cập Flow.google.com...")
                try:
                    self.page.goto(config.FLOW_URL, wait_until="networkidle", timeout=60000)
                except PlaywrightTimeout:
                    raise Exception("Không thể truy cập Flow.google.com. Kiểm tra kết nối mạng.")

                # Kiểm tra đã đăng nhập chưa
                if self._is_login_required():
                    raise Exception(
                        "Cookies hết hiệu lực hoặc chưa đăng nhập. "
                        "Vui lòng bấm 'Export cookies từ Chrome' hoặc 'Import cookies JSON' lại."
                    )

                # Upload ảnh nếu có
                if image_path and os.path.exists(image_path):
                    update_progress(3, 8, "🖼️ Đang upload ảnh tham chiếu...")
                    self._upload_image(image_path)

                # Nhập prompt
                update_progress(4, 8, "✍️ Nhập prompt...")
                self._fill_prompt(prompt)

                # Chọn model
                update_progress(5, 8, f"⚙️ Chọn model: {model}...")
                self._select_model(model)

                # Chọn duration
                update_progress(6, 8, f"⏱️ Chọn thời lượng: {duration}...")
                self._select_duration(duration)

                # Click generate
                update_progress(7, 8, "🎬 Đang tạo video (có thể mất vài phút)...")
                self._click_generate()

                # Chờ video xuất hiện
                update_progress(8, 8, "⏳ Chờ video render xong...")
                video_url = self._wait_for_video()

                # Tải video về
                update_progress(9, 9, "💾 Đang tải video về máy...")  # Bước 9/9
                downloaded_path = self._download_video(video_url)

                return downloaded_path
            finally:
                try:
                    if self.browser:
                        self.browser.close()
                except Exception:
                    pass

    def _upload_image(self, image_path: str):
        """Upload ảnh lên Flow"""
        abs_path = os.path.abspath(image_path)
        if not os.path.exists(abs_path):
            raise Exception(f"Không tìm thấy ảnh: {abs_path}")

        try:
            # Tìm input file
            file_input = self.page.locator('input[type="file"]').first
            if file_input.count() > 0:
                file_input.wait_for(state="visible", timeout=10000)
                file_input.set_input_files(abs_path)
                self._log(f"   Đã upload ảnh: {abs_path}")
                self.page.wait_for_timeout(1500)
                return

            # Nếu không có input file visible, thử tìm nút upload và click
            upload_btn = self.page.locator(config.SELECTORS["upload_button"]).first
            if upload_btn.count() > 0 and upload_btn.is_visible():
                upload_btn.click()
                self.page.wait_for_timeout(500)
                file_input = self.page.locator('input[type="file"]').first
                if file_input.count() > 0:
                    file_input.set_input_files(abs_path)
                    self._log(f"   Đã upload ảnh: {abs_path}")
                    self.page.wait_for_timeout(1500)
                    return

            raise Exception("Không tìm thấy nút upload ảnh trên Flow.")
        except Exception as e:
            raise Exception(f"Lỗi upload ảnh: {e}")

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
