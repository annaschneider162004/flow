# Flow Video Generator Desktop App

Desktop app tự động tạo video bằng tài khoản Flow Google (gói Ultra) sử dụng Playwright + PyQt6.

## Tính năng

- Giao diện nhập prompt
- Chọn model (Veo 3 Fast, Quality, Veo 2...)
- Chọn thời lượng
- Chạy Playwright tự động tạo video
- Hiển thị tiến độ
- Tải video về máy

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

### Lần đầu tiên

1. Bấm **"Đăng nhập Flow"**
2. Trình duyệt Chrome sẽ mở flow.google.com
3. Đăng nhập Google account có gói Flow Ultra
4. Đóng trình duyệt khi đăng nhập xong
5. Lần sau app sẽ tự dùng lại phiên đăng nhập

### Tạo video

1. Nhập prompt
2. Chọn model và thời lượng
3. Bấm **"Tạo Video"**
4. Chờ video render xong và tải về

## Lưu ý

- Google Flow chưa có API chính thức, tool dùng browser automation.
- Nếu Flow thay đổi giao diện, hãy cập nhật các selector trong `config.py`.
- Đảm bảo tài khoản có đủ credits Ultra để tạo video.
- Không nên chạy quá nhanh liên tục để tránh bị Google giới hạn.

## Sửa selector nếu Flow update

Mở `config.py` và chỉnh các giá trị trong `SELECTORS` cho khớp với DOM hiện tại của flow.google.com.
