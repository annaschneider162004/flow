import os
import sys
import config
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QTextEdit,
    QProgressBar, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from flow_automation import FlowAutomation
from manifest_parser import generate_prompt_from_manifest_file
from cookie_importer import import_cookies_from_json, import_cookies_from_netscape_txt


class GenerateThread(QThread):
    progress = pyqtSignal(int, int, str)
    log = pyqtSignal(str)
    finished_success = pyqtSignal(str)
    finished_error = pyqtSignal(str)

    def __init__(self, prompt, model, duration, image_path=None):
        super().__init__()
        self.prompt = prompt
        self.model = model
        self.duration = duration
        self.image_path = image_path

    def run(self):
        try:
            def on_progress(step, total, msg):
                self.progress.emit(step, total, msg)

            def on_log(msg):
                self.log.emit(msg)

            bot = FlowAutomation(log_callback=on_log)
            path = bot.generate_video(
                prompt=self.prompt,
                model=self.model,
                duration=self.duration,
                image_path=self.image_path,
                progress_callback=on_progress
            )
            self.finished_success.emit(path)
        except Exception as e:
            self.finished_error.emit(str(e))


class ExportCookiesThread(QThread):
    log = pyqtSignal(str)
    finished = pyqtSignal()

    def run(self):
        try:
            bot = FlowAutomation(log_callback=lambda msg: self.log.emit(msg))
            bot.export_cookies_from_chrome()
        except Exception as e:
            self.log.emit(f"❌ Lỗi: {e}")
        finally:
            self.finished.emit()


class FlowVideoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flow Video Generator - V31")
        self.setMinimumSize(750, 750)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setSpacing(15)

        # Title
        title = QLabel("🎬 Flow Video Generator - V31")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1a73e8;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(title)

        subtitle = QLabel("Tự động tạo video bằng tài khoản Flow Google Ultra")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(subtitle)

        # Auth status
        self.auth_label = QLabel(self._get_auth_status_text())
        self.auth_label.setWordWrap(True)
        self.auth_label.setStyleSheet("padding: 8px; background-color: #f0f0f0; border-radius: 5px;")
        self.layout.addWidget(self.auth_label)

        # Mode selection
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Chế độ:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(config.GENERATION_MODES)
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        self.layout.addLayout(mode_layout)

        # Image selection (for image-to-video)
        image_layout = QHBoxLayout()
        self.image_label = QLabel("🖼️ Ảnh tham chiếu: (chưa chọn)")
        self.image_label.setWordWrap(True)
        image_layout.addWidget(self.image_label)
        self.image_btn = QPushButton("Chọn ảnh / manifest")
        self.image_btn.clicked.connect(self.select_image)
        image_layout.addWidget(self.image_btn)
        self.layout.addLayout(image_layout)

        # Generate prompt from manifest button
        self.manifest_btn = QPushButton("✨ Sinh prompt từ manifest")
        self.manifest_btn.clicked.connect(self.generate_prompt_from_manifest)
        self.manifest_btn.setEnabled(False)
        self.layout.addWidget(self.manifest_btn)

        # Prompt input
        self.layout.addWidget(QLabel("📝 Prompt mô tả video:"))
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Mô tả chi tiết video bạn muốn tạo...")
        self.prompt_input.setMinimumHeight(120)
        self.layout.addWidget(self.prompt_input)

        # Settings row
        settings_layout = QHBoxLayout()

        settings_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(config.AVAILABLE_MODELS)
        settings_layout.addWidget(self.model_combo)

        settings_layout.addWidget(QLabel("Thời lượng:"))
        self.duration_combo = QComboBox()
        self.duration_combo.addItems(config.AVAILABLE_DURATIONS)
        settings_layout.addWidget(self.duration_combo)

        self.layout.addLayout(settings_layout)

        # Download folder
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel(f"📁 Thư mục tải về: {config.DOWNLOAD_DIR}")
        self.folder_label.setWordWrap(True)
        folder_layout.addWidget(self.folder_label)
        
        self.folder_btn = QPushButton("Đổi thư mục")
        self.folder_btn.clicked.connect(self.change_folder)
        folder_layout.addWidget(self.folder_btn)
        self.layout.addLayout(folder_layout)

        # Buttons
        btn_layout = QHBoxLayout()

        self.export_btn = QPushButton("🍪 Export cookies từ Chrome")
        self.export_btn.setStyleSheet("font-size: 13px; padding: 8px;")
        self.export_btn.clicked.connect(self.run_export_cookies)
        btn_layout.addWidget(self.export_btn)

        self.import_cookie_btn = QPushButton("📥 Import cookies JSON/TXT")
        self.import_cookie_btn.setStyleSheet("font-size: 13px; padding: 8px;")
        self.import_cookie_btn.clicked.connect(self.run_import_cookies)
        btn_layout.addWidget(self.import_cookie_btn)

        self.generate_btn = QPushButton("🎬 Tạo Video")
        self.generate_btn.setStyleSheet(
            "font-size: 14px; padding: 10px; background-color: #1a73e8; color: white; font-weight: bold;"
        )
        self.generate_btn.clicked.connect(self.run_generate)
        btn_layout.addWidget(self.generate_btn)

        self.layout.addLayout(btn_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Sẵn sàng. Nếu chưa export cookies, hãy bấm 'Export cookies từ Chrome' trước.")
        self.status_label.setWordWrap(True)
        self.layout.addWidget(self.status_label)

        # Log output
        self.layout.addWidget(QLabel("📋 Nhật ký:"))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(150)
        self.layout.addWidget(self.log_output)

        self.selected_image_path = None
        self.on_mode_changed(config.GENERATION_MODES[0])

    def _get_auth_status_text(self):
        if os.path.exists(config.AUTH_STATE_FILE):
            return f"✅ Đã có cookies: {config.AUTH_STATE_FILE}"
        return f"⚠️ Chưa có cookies. Hãy bấm 'Export cookies từ Chrome' hoặc 'Import cookies JSON' trước."

    def update_auth_status(self):
        self.auth_label.setText(self._get_auth_status_text())

    def log(self, message: str):
        self.log_output.append(message)
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def on_mode_changed(self, mode):
        is_image_mode = (mode == "image-to-video")
        self.image_label.setEnabled(is_image_mode)
        self.image_btn.setEnabled(is_image_mode)
        if not is_image_mode:
            self.selected_image_path = None
            self.image_label.setText("🖼️ Ảnh tham chiếu: (không dùng ở chế độ text)")
            self.manifest_btn.setEnabled(False)

    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn ảnh hoặc manifest JSON",
            "",
            "Images (*.png *.jpg *.jpeg *.webp);;JSON Manifest (*.json);;All Files (*)"
        )
        if file_path:
            self.selected_image_path = file_path
            self.image_label.setText(f"🖼️ Ảnh tham chiếu: {file_path}")
            self.manifest_btn.setEnabled(file_path.lower().endswith(".json"))

    def generate_prompt_from_manifest(self):
        if not self.selected_image_path or not self.selected_image_path.lower().endswith(".json"):
            QMessageBox.warning(self, "Chưa chọn manifest", "Vui lòng chọn file JSON manifest trước.")
            return
        try:
            prompt = generate_prompt_from_manifest_file(self.selected_image_path)
            self.prompt_input.setPlainText(prompt)
            self.log("✨ Đã sinh prompt từ manifest")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể sinh prompt:\n{e}")

    def change_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục tải video về")
        if folder:
            config.DOWNLOAD_DIR = folder
            self.folder_label.setText(f"📁 Thư mục tải về: {folder}")

    def run_export_cookies(self):
        self.export_btn.setEnabled(False)
        self.generate_btn.setEnabled(False)
        self.import_cookie_btn.setEnabled(False)
        self.status_label.setText("Đang mở Chrome để export cookies...")

        self.export_thread = ExportCookiesThread()
        self.export_thread.log.connect(self.log)
        self.export_thread.finished.connect(self.on_export_finished)
        self.export_thread.start()

    def on_export_finished(self):
        self.export_btn.setEnabled(True)
        self.generate_btn.setEnabled(True)
        self.import_cookie_btn.setEnabled(True)
        self.update_auth_status()
        if os.path.exists(config.AUTH_STATE_FILE):
            self.status_label.setText(f"✅ Đã export cookies: {config.AUTH_STATE_FILE}")
        else:
            self.status_label.setText("❌ Export cookies thất bại. Kiểm tra nhật ký.")

    def run_import_cookies(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn file cookies",
            "",
            "JSON Files (*.json);;Netscape TXT (*.txt);;All Files (*)"
        )
        if not file_path:
            return

        try:
            if file_path.lower().endswith(".txt"):
                count = import_cookies_from_netscape_txt(file_path, config.AUTH_STATE_FILE)
            else:
                count = import_cookies_from_json(file_path, config.AUTH_STATE_FILE)
            self.update_auth_status()
            self.status_label.setText(f"✅ Đã import {count} cookies từ {file_path}")
            self.log(f"✅ Đã import {count} cookies từ {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi import cookies", f"{e}")

    def run_generate(self):
        if not os.path.exists(config.AUTH_STATE_FILE):
            QMessageBox.warning(
                self,
                "Chưa có cookies",
                "Vui lòng bấm 'Export cookies từ Chrome' hoặc 'Import cookies JSON' trước khi tạo video."
            )
            return

        mode = self.mode_combo.currentText()
        image_path = self.selected_image_path if mode == "image-to-video" else None

        if mode == "image-to-video" and (not image_path or not os.path.exists(image_path)):
            QMessageBox.warning(self, "Thiếu ảnh", "Vui lòng chọn ảnh tham chiếu ở chế độ image-to-video.")
            return

        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Thiếu prompt", "Vui lòng nhập prompt mô tả video.")
            return

        model = self.model_combo.currentText()
        duration = self.duration_combo.currentText()

        self.generate_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.import_cookie_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("🚀 Đang bắt đầu tạo video...")

        self.gen_thread = GenerateThread(prompt, model, duration, image_path)
        self.gen_thread.log.connect(self.log)
        self.gen_thread.progress.connect(self.update_progress)
        self.gen_thread.finished_success.connect(self.on_generate_success)
        self.gen_thread.finished_error.connect(self.on_generate_error)
        self.gen_thread.start()

    def update_progress(self, step, total, message):
        percent = int((step / total) * 100)
        self.progress_bar.setValue(percent)
        self.status_label.setText(message)

    def on_generate_success(self, filepath):
        self.generate_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        self.import_cookie_btn.setEnabled(True)
        self.status_label.setText(f"✅ Hoàn tất! Video lưu tại: {filepath}")
        self.log(f"🎉 Tải video thành công: {filepath}")
        QMessageBox.information(self, "Thành công", f"Video đã được lưu tại:\n{filepath}")

    def on_generate_error(self, error):
        self.generate_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        self.import_cookie_btn.setEnabled(True)
        self.status_label.setText(f"❌ Lỗi: {error}")
        self.log(f"❌ Lỗi: {error}")
        QMessageBox.critical(self, "Lỗi", f"Đã xảy ra lỗi:\n{error}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FlowVideoApp()
    window.show()
    sys.exit(app.exec())
