# Flow Video Generator - V31

Desktop app tự động tạo video bằng tài khoản Flow Google (gói Ultra) sử dụng Playwright + PyQt6.

## Tính năng V31

- ✅ Giao diện nhập prompt
- ✅ Chọn model (Veo 3 Fast, Quality, Veo 2...)
- ✅ Chọn thời lượng
- ✅ **Image-to-video**: upload ảnh tham chiếu để tạo video
- ✅ **Auto prompt từ manifest**: đọc file JSON manifest và sinh prompt tự động
- ✅ **Export cookies từ Chrome profile**
- ✅ **Import cookies từ file JSON/TXT** (Netscape format)
- ✅ Chạy Playwright tự động tạo video
- ✅ Hiển thị tiến độ
- ✅ Tải video về máy

## Cài đặt

```bash
# 1. Cài Python 3.10+
# 2. Cài thư viện
pip install -r requirements.txt

# 3. Cài browser cho Playwright
playwright install chromium
```

## Cách dùng

```bash
python main.py
```

### 1. Chuẩn bị đăng nhập (chọn 1 trong 2)

#### A. Export cookies từ Chrome profile
1. Sửa `config.py` cho đúng đường dẫn Chrome và profile:
   ```python
   CHROME_EXECUTABLE_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
   CHROME_USER_DATA_DIR = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
   CHROME_PROFILE_NAME = "Default"  # hoặc "Profile 1"
   ```
2. Bấm **"Export cookies từ Chrome"**
3. Chrome mở ra, đăng nhập Flow
4. Đóng trình duyệt → cookies được lưu vào `flow_auth.json`

#### B. Import cookies từ file JSON/TXT
1. Bấm **"Import cookies JSON/TXT"**
2. Chọn file cookies (định dạng Playwright storage state, Netscape TXT, hoặc danh sách JSON cookies)
3. Tool tự động chuyển thành `flow_auth.json`

### 2. Tạo video

#### Text-to-video
1. Chọn chế độ **"text-to-video"**
2. Nhập prompt
3. Chọn model + thời lượng
4. Bấm **"Tạo Video"**

#### Image-to-video
1. Chọn chế độ **"image-to-video"**
2. Bấm **"Chọn ảnh / manifest"** → chọn file ảnh PNG/JPG/WEBP
3. (Tùy chọn) Nếu chọn file JSON manifest, bấm **"Sinh prompt từ manifest"** để tự động tạo prompt
4. Chọn model + thời lượng
5. Bấm **"Tạo Video"**

## Lưu ý

- Google Flow chưa có API chính thức, tool dùng browser automation.
- Nếu Flow thay đổi giao diện, hãy cập nhật các selector trong `config.py`.
- Đảm bảo tài khoản có đủ credits Ultra để tạo video.
- Không nên chạy quá nhanh liên tục để tránh bị Google giới hạn.
- File `flow_auth.json` chứa thông tin đăng nhập, không đẩy lên GitHub công khai.
