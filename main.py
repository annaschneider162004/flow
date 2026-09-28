import sys
import config
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QTextEdit,
    QProgressBar, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from flow_automation import FlowAutomation


class GenerateThread(QThread):
    progress = pyqtSignal(int, int, str)
    log = pyqtSignal(str)
    finished_success = pyqtSignal(str)
    finished_error = pyqtSignal(str)

    def __init__(self, prompt, model, duration):
        super().__init__()
        self.prompt = prompt
        self.model = model
        self.duration = duration

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
                progress_callback=on_progress
            )
            self.finished_success.emit(path)
        except Exception as e:
            self.finished_error.emit(str(e))


class SetupLoginThread(QThread):
    log = pyqtSignal(str)
    finished = pyqtSignal()

    def run(self):
        try:
            bot = FlowAutomation(log_callback=lambda msg: self.log.emit(msg))
            bot.setup_login()
        except Exception as e:
            self.log.emit(f"❌ Lỗi: {e}")
        finally:
            self.finished.emit()


class FlowVideoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flow Video Generator")
        self.setMinimumSize(700, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setSpacing(15)

        # Title
        title = QLabel("🎬 Flow Video Generator")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1a73e8;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(title)

        subtitle = QLabel("Tự động tạo video bằng tài khoản Flow Google Ultra")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(subtitle)

        # Prompt input
        self.layout.addWidget(QLabel("📝 Prompt mô tả video:"))
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Mô tả chi tiết video bạn muốn tạo...")
        self.prompt_input.setMinimumHeight(100)
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

        self.login_btn = QPushButton("🔑 Đăng nhập Flow (lần đầu)")
        self.login_btn.setStyleSheet("font-size: 14px; padding: 10px;")
        self.login_btn.clicked.connect(self.run_setup_login)
        btn_layout.addWidget(self.login_btn)

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
        self.status_label = QLabel("Sẵn sàng. Nếu chưa đăng nhập, hãy bấm 'Đăng nhập Flow' trước.")
        self.status_label.setWordWrap(True)
        self.layout.addWidget(self.status_label)

        # Log output
        self.layout.addWidget(QLabel("📋 Nhật ký:"))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(150)
        self.layout.addWidget(self.log_output)

    def log(self, message: str):
        self.log_output.append(message)
        # Auto scroll
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def change_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục tải video về")
        if folder:
            config.DOWNLOAD_DIR = folder
            self.folder_label.setText(f"📁 Thư mục tải về: {folder}")

    def run_setup_login(self):
        self.login_btn.setEnabled(False)
        self.generate_btn.setEnabled(False)
        self.status_label.setText("Đang mở trình duyệt để đăng nhập...")

        self.login_thread = SetupLoginThread()
        self.login_thread.log.connect(self.log)
        self.login_thread.finished.connect(self.on_login_finished)
        self.login_thread.start()

    def on_login_finished(self):
        self.login_btn.setEnabled(True)
        self.generate_btn.setEnabled(True)
        self.status_label.setText("✅ Đã lưu đăng nhập. Bạn có thể tạo video ngay bây giờ.")

    def run_generate(self):
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Thiếu prompt", "Vui lòng nhập prompt mô tả video.")
            return

        model = self.model_combo.currentText()
        duration = self.duration_combo.currentText()

        self.generate_btn.setEnabled(False)
        self.login_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("🚀 Đang bắt đầu tạo video...")

        self.gen_thread = GenerateThread(prompt, model, duration)
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
        self.login_btn.setEnabled(True)
        self.status_label.setText(f"✅ Hoàn tất! Video lưu tại: {filepath}")
        self.log(f"🎉 Tải video thành công: {filepath}")
        QMessageBox.information(self, "Thành công", f"Video đã được lưu tại:\n{filepath}")

    def on_generate_error(self, error):
        self.generate_btn.setEnabled(True)
        self.login_btn.setEnabled(True)
        self.status_label.setText(f"❌ Lỗi: {error}")
        self.log(f"❌ Lỗi: {error}")
        QMessageBox.critical(self, "Lỗi", f"Đã xảy ra lỗi:\n{error}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FlowVideoApp()
    window.show()
    sys.exit(app.exec())
