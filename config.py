# ============================================================
# CẤU HÌNH SELECTOR CỦA FLOW.GOOGLE.COM
# Nếu Flow cập nhật giao diện, bạn chỉ cần sửa các selector này
# ============================================================

# URL trang tạo video của Flow
FLOW_URL = "https://flow.google.com/media/generate"

# Thư mục lưu profile đăng nhập để lần sau không cần nhập lại
USER_DATA_DIR = "./flow_profile"

# Thư mục tải video về
DOWNLOAD_DIR = "./downloads"

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
