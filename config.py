# ============================================================
# CẤU HÌNH CHROME PROFILE VÀ SELECTOR CỦA FLOW.GOOGLE.COM
# ============================================================

import os

# URL trang tạo video của Flow
FLOW_URL = "https://flow.google.com/media/generate"

# ============================================================
# CẤU HÌNH CHROME PROFILE (dùng để export cookies)
# ============================================================

# Đường dẫn đến file chrome.exe trên máy Windows
CHROME_EXECUTABLE_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# Thư mục User Data của Chrome
CHROME_USER_DATA_DIR = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")

# Tên profile Chrome muốn dùng: "Default", "Profile 1", "Profile 2", ...
CHROME_PROFILE_NAME = "Default"

# File lưu cookies/storage state sau khi export
AUTH_STATE_FILE = "flow_auth.json"

# Thư mục tải video về
DOWNLOAD_DIR = "./downloads"

# Profile cũ (backup)
USER_DATA_DIR = "./flow_profile"

# Các selector giao diện (có thể thay đổi nếu Flow update)
SELECTORS = {
    # Ô nhập prompt
    "prompt_input": 'textarea[placeholder*="prompt" i], textarea[aria-label*="prompt" i], textarea',
    
    # Nút tạo video (Generate / Create)
    "generate_button": 'button:has-text("Generate"), button:has-text("Create"), button[aria-label*="generate" i]',
    
    # Dropdown chọn duration / thời lượng
    "duration_dropdown": 'button:has-text("Duration"), button:has-text("seconds"), [role="combobox"]:has-text("s")',
    
    # Dropdown chọn model / chất lượng
    "model_dropdown": 'button:has-text("Model"), button:has-text("Quality"), button:has-text("Fast")',
    
    # Element video kết quả xuất hiện sau khi tạo xong
    "result_video": 'video, [data-test-id="generated-video"], a[href*=".mp4"], source[src*=".mp4"]',
    
    # Nút download video
    "download_button": 'button:has-text("Download"), button[aria-label*="download" i], a[download]',
}

# Thời gian chờ tối đa (giây)
MAX_WAIT_TIME = 600  # 10 phút

# Các model có thể có trên Flow
AVAILABLE_MODELS = [
    "Veo 3 Fast",
    "Veo 3 Quality", 
    "Veo 2",
]

# Các thời lượng có thể có
AVAILABLE_DURATIONS = [
    "5s",
    "8s",
    "10s",
    "12s",
]
