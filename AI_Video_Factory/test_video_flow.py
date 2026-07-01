# -*- coding: utf-8 -*-
import sys
import os
import time
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QFileDialog, QMessageBox, QComboBox, QTextEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from playwright.sync_api import sync_playwright

# Import các tài nguyên sẵn có trong project của bạn
from core.config_manager import ConfigManager
from core.browser_manager import BrowserManager
from pages.flow_components_page import FlowComponentsPage

# =======================================================
# QTHREAD: LUỒNG CHẠY PLAYWRIGHT NGẦM (TRÁNH ĐƠ UI)
# =======================================================
class TestVideoComponentsWorker(QThread):
    log_signal = pyqtSignal(str, str) # Phát tin nhắn log: (message, status)
    finished_signal = pyqtSignal(str, str) # Phát kết quả: (status, video_path)

    def __init__(self, profile, image_paths, prompt, save_dir, model_type):
        super().__init__()
        self.profile = profile
        self.image_paths = image_paths
        self.prompt = prompt
        self.save_dir = save_dir
        self.model_type = model_type

    def run(self):
        self.log_signal.emit(f"🚀 Khởi tạo BrowserManager cho nick: {self.profile}", "INFO")
        
        try:
            with sync_playwright() as p:
                bm = BrowserManager(profile_name=self.profile)
                
                # Headless=False để chúng ta nhìn thấy mắt Chrome tự click gõ phím
                context = bm.init_browser(p, headless=False)
                page = context.pages[0]
                
                self.log_signal.emit("🌐 Đang truy cập Google Flow...", "INFO")
                bot = FlowComponentsPage(page)
                
                # Ép log từ bot sang UI Test
                bot.write_flow_log = lambda step, msg, status="INFO": self.log_signal.emit(f"[Step {step}] {msg}", status)
                
                bot.navigate()
                
                self.log_signal.emit("🎬 Bắt đầu quy trình tự động hóa create_video_components...", "INFO")
                result = bot.create_video_components(
                    image_paths=self.image_paths,
                    prompt_text=self.prompt,
                    save_dir=self.save_dir,
                    profile_name=self.profile,
                    sku="TEST_SKU",
                    model_type=self.model_type,
                    batch_id=f"Test_{datetime.now().strftime('%H%M%S')}"
                )
                
                context.close()
                bm.cleanup_profile()
                
                if result and result.endswith(".mp4"):
                    self.finished_signal.emit("SUCCESS", result)
                else:
                    self.finished_signal.emit("FAIL", str(result))
                    
        except Exception as e:
            self.log_signal.emit(f"❌ Crash hệ thống: {e}", "FAIL")
            self.finished_signal.emit("CRASH", str(e))

# =======================================================
# UI TEST CHÍNH
# =======================================================
class VideoTestApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VEO3 - BỘ THỬ NGHIỆM PLAYWRIGHT VIDEO FLOW")
        self.resize(1100, 800)
        self.mgr = ConfigManager()
        self.image_inputs = []
        self.worker = None
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(12)

        # Style chuyên nghiệp tối giản
        self.setStyleSheet("""
            QMainWindow { background-color: #0b0d14; }
            QLabel { color: #aaa; font-weight: bold; font-size: 13px; }
            QLineEdit, QComboBox, QTextEdit { 
                background-color: #161926; color: #eee; border: 1px solid #333; 
                border-radius: 6px; padding: 8px; font-size: 13px;
            }
            QPushButton {
                background-color: #4CAF50; color: white; font-weight: bold;
                font-size: 14px; border: none; border-radius: 6px; padding: 8px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)

        # --- PHẦN 1: CHỌN NICK & MODEL ---
        top_layout = QHBoxLayout()
        
        top_layout.addWidget(QLabel("👤 Chọn Tài Khoản:"))
        self.cb_profile = QComboBox()
        self.cb_profile.addItems(self.mgr.get_all_profiles())
        top_layout.addWidget(self.cb_profile, 1)

        top_layout.addWidget(QLabel("🤖 Bản Model:"))
        self.cb_model = QComboBox()
        self.cb_model.addItems(["Lite", "Pro"])
        top_layout.addWidget(self.cb_model, 1)
        
        layout.addLayout(top_layout)

        # --- PHẦN 2: CHỌN SỐ LƯỢNG ẢNH ĐỘNG ---
        img_config_layout = QHBoxLayout()
        img_config_layout.addWidget(QLabel("📸 Số lượng ảnh tham chiếu cần test:"))
        self.cb_num_images = QComboBox()
        self.cb_num_images.addItems(["2", "3", "1"])
        self.cb_num_images.currentIndexChanged.connect(self.on_num_images_changed)
        img_config_layout.addWidget(self.cb_num_images)
        img_config_layout.addStretch()
        layout.addLayout(img_config_layout)

        # Container chứa các dòng chọn đường dẫn ảnh
        self.images_container = QWidget()
        self.images_layout = QVBoxLayout(self.images_container)
        self.images_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.images_container)

        # --- PHẦN 3: NHẬP PROMPT & THƯ MỤC LƯU ---
        layout.addWidget(QLabel("✍️ NHẬP PROMPT (Hỗ trợ chèn các biến {IMG_1}, {IMG_2}...):"))
        self.txt_prompt = QTextEdit()
        self.txt_prompt.setPlaceholderText("Ví dụ: {IMG_1} standing inside {IMG_2}. Background lock... Dialogue: 'Outfit hôm nay xinh xỉu các bà ơi'")
        self.txt_prompt.setText("{IMG_1} standing inside {IMG_2}. Background lock: same environment from {IMG_2}. Realistic TikTok clothing review style. Dialogue: 'Trời ơi cái áo này mặc lên nhìn gọn người ghê...'")
        self.txt_prompt.setMaximumHeight(100)
        layout.addWidget(self.txt_prompt)

        # Chọn thư mục lưu
        save_layout = QHBoxLayout()
        self.txt_save_dir = QLineEdit()
        self.txt_save_dir.setPlaceholderText("Đường dẫn lưu video...")
        
        # Thử lấy đường dẫn lưu cấu hình cũ từ database
        saved_dir = self.mgr.get_components_save_dir()
        self.txt_save_dir.setText(saved_dir)

        btn_browse = QPushButton("📁 Browse")
        btn_browse.clicked.connect(self.browse_save_dir)
        save_layout.addWidget(QLabel("💾 Lưu tại:"))
        save_layout.addWidget(self.txt_save_dir, 1)
        save_layout.addWidget(btn_browse)
        layout.addLayout(save_layout)

        # --- PHẦN 4: NÚT CHẠY TEST ---
        self.btn_run = QPushButton("🚀 BẮT ĐẦU CHẠY THỬ NGHIỆM TRÌNH DUYỆT (PLAYWRIGHT)")
        self.btn_run.setMinimumHeight(45)
        self.btn_run.setStyleSheet("background-color: #9C27B0; color: white; font-weight: bold; font-size: 15px;")
        self.btn_run.clicked.connect(self.run_automation_test)
        layout.addWidget(self.btn_run)

        # --- PHẦN 5: CONSOLE LOG HIỂN THỊ REAL-TIME ---
        layout.addWidget(QLabel("📋 TIẾN TRÌNH CHẠY LOG REAL-TIME:"))
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet("background-color: #0b0d14; color: #4CAF50; font-family: 'Consolas'; font-size: 12px;")
        layout.addWidget(self.txt_log, 1)

        # Khởi tạo ô ảnh lần đầu (mặc định 2 ảnh)
        self.on_num_images_changed()

    def on_num_images_changed(self):
        """Thay đổi động số ô chọn ảnh trên giao diện"""
        count = int(self.cb_num_images.currentText())
        for i in reversed(range(self.images_layout.count())):
            widget = self.images_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
        
        self.image_inputs.clear()
        for i in range(count):
            row = QHBoxLayout()
            lbl = QLabel(f"Ảnh {i+1} {{IMG_{i+1}}}:")
            lbl.setFixedWidth(100)
            txt = QLineEdit()
            txt.setPlaceholderText(f"Bấm Browse bên cạnh để chọn ảnh {i+1}...")
            
            # Tự động gợi ý file có sẵn để bạn test nhanh
            btn = QPushButton("Duyệt")
            btn.setFixedWidth(60)
            btn.clicked.connect(lambda checked, t=txt: self.browse_image(t))
            
            row.addWidget(lbl)
            row.addWidget(txt)
            row.addWidget(btn)
            
            row_widget = QWidget()
            row_widget.setLayout(row)
            self.images_layout.addWidget(row_widget)
            self.image_inputs.append(txt)

    def browse_image(self, line_edit):
        path, _ = QFileDialog.getOpenFileName(self, "Chọn ảnh", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if path:
            line_edit.setText(os.path.normpath(path))

    def browse_save_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu Output", self.txt_save_dir.text())
        if folder:
            self.txt_save_dir.setText(os.path.normpath(folder))
            self.mgr.set_components_save_dir(folder)

    def log(self, message, status="INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        color = "#4CAF50" # Xanh mặc định
        if status == "FAIL" or status == "ERROR": color = "red"
        elif status == "WARN": color = "orange"
        
        self.txt_log.append(f"<font color='gray'>[{ts}]</font> <font color='{color}'><b>[{status}]</b> {message}</font>")

    def run_automation_test(self):
        # Thu thập ảnh
        img_paths = [txt.text().strip() for txt in self.image_inputs if txt.text().strip()]
        if len(img_paths) < int(self.cb_num_images.currentText()):
            QMessageBox.warning(self, "Thiếu ảnh", "Vui lòng chọn đầy đủ đường dẫn ảnh để test!")
            return

        prompt = self.txt_prompt.toPlainText().strip()
        save_dir = self.txt_save_dir.text().strip()
        if not prompt or not save_dir:
            QMessageBox.warning(self, "Thiếu thông tin", "Hãy điền Prompt và chọn Thư mục lưu trước!")
            return

        self.txt_log.clear()
        self.btn_run.setEnabled(False)

        # KHỞI CHẠY THỢ PLAYWRIGHT NGẦM
        self.worker = TestVideoComponentsWorker(
            profile=self.cb_profile.currentText(),
            image_paths=img_paths,
            prompt=prompt,
            save_dir=save_dir,
            model_type=self.cb_model.currentText()
        )
        self.worker.log_signal.connect(self.log)
        self.worker.finished_signal.connect(self.on_test_finished)
        self.worker.start()

    def on_test_finished(self, status, result_path):
        self.btn_run.setEnabled(True)
        if status == "SUCCESS":
            self.log(f"🎉 RENDER HOÀN TẤT THÀNH CÔNG!", "OK")
            self.log(f"💾 File video được lưu tại: {result_path}", "OK")
            QMessageBox.information(self, "Thành công", f"Video đã được tạo và lưu thành công tại:\n{result_path}")
        else:
            self.log(f"❌ RENDER THẤT BẠI! Lỗi chi tiết: {result_path}", "FAIL")
            QMessageBox.critical(self, "Thất bại", f"Lỗi trong quá trình render: {result_path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoTestApp()
    window.show()
    sys.exit(app.exec())