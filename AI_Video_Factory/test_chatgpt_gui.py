import sys, os, time, re
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFileDialog, QTextEdit, QLineEdit)
from PyQt6.QtCore import QThread, pyqtSignal
from playwright.sync_api import sync_playwright

# Import trang ChatGPTImagesPage từ project của bạn
from pages.chatgpt_images_page import ChatGPTImagesPage

class TestWorker(QThread):
    finished = pyqtSignal()

    def __init__(self, identity_img, outfit_img, bg_img, prompt, save_dir):
        super().__init__()
        # Gom lại theo đúng thứ tự 1, 2, 3 để nạp vào ChatGPT
        self.imgs = [identity_img, outfit_img, bg_img]
        self.prompt = prompt
        self.save_dir = save_dir

    def run(self):
        # 1. CẤU HÌNH ĐƯỜNG DẪN TRÌNH DUYỆT VÀ PROFILE
        chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        # Trỏ vào google_acc_3 như yêu cầu của bạn
        profile_path = os.path.normpath(os.path.join(os.getcwd(), "profiles", "google_acc_4"))
        
        with sync_playwright() as p:
            try:
                # 2. KHỞI CHẠY PERSISTENT CONTEXT (DÙNG PROFILE CÓ SẴN)
                context = p.chromium.launch_persistent_context(
                    user_data_dir=profile_path,
                    executable_path=chrome_exe,
                    headless=False,
                    slow_mo=500, # Đủ chậm để bạn nhìn thấy các khung đỏ (Highlight)
                    no_viewport=True,
                    args=['--disable-blink-features=AutomationControlled']
                )
                
                page = context.pages[0] 
                bot = ChatGPTImagesPage(page)
                bot.navigate()

                # 3. QUY TRÌNH THỰC THI TEST
                print(f"🚀 Bắt đầu quy trình Test trên Nick: google_acc_3")
                
                # Bước 1: Nạp 3 ảnh qua Menu (+)
                if bot.upload_references(self.imgs):
                    
                    # Bước 2: Tạo Ảnh A (Frame đầu)
                    # Cần truyền đủ 3 tham số: prompt, save_path, step_label
                    path_a = os.path.join(self.save_dir, "Result_A.jpg")
                    bot.generate_step(self.prompt, path_a, "Shot A")
                    
                    # Bước 3: Tạo Ảnh B (Frame cuối - Đổi tư thế)
                    # Tiếp nối đoạn chat để giữ nguyên nhân vật
                    path_b = os.path.join(self.save_dir, "Result_B.jpg")
                    pose_req = "Maintain the same girl, same outfit, and same room. Change her standing pose to be more alluring and charming. Stand still."
                    bot.generate_step(pose_req, path_b, "Shot B")

                print("✅ [TEST] Đã hoàn thành xong 2 lượt tạo ảnh.")
                context.close()
                
            except Exception as e:
                print(f"❌ [TEST-ERROR] Lỗi hệ thống: {e}")
                
            self.finished.emit()

class QuickTestApp(QWidget):
    def __init__(self):
        super().__init__()
        self.paths = {"id": "", "outfit": "", "bg": ""}
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("VEO3 - CHATGPT IMAGE PRODUCTION TESTER")
        self.resize(700, 650)
        self.setStyleSheet("""
            QWidget { background-color: #0f111a; color: #eee; font-family: Segoe UI; }
            QPushButton { background-color: #1a1d29; border: 1px solid #30364d; border-radius: 8px; padding: 12px; min-height: 20px;}
            QPushButton:hover { background-color: #252a3d; border-color: #4CAF50; }
            QLineEdit { background-color: #05060a; border: 1px solid #252a3d; padding: 10px; color: #00ff00; border-radius: 5px; }
            QTextEdit { background-color: #000; color: #4CAF50; font-family: Consolas; font-size: 12px; border-radius: 5px; }
            QLabel { font-weight: bold; margin-top: 5px; }
        """)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("📂 CHỌN NGUYÊN LIỆU (THỨ TỰ 1-2-3):"))
        
        self.btn_id = self._create_pick_btn("👤 Bước 1: Chọn Ảnh Danh Tính (Identity)", "id")
        self.btn_outfit = self._create_pick_btn("👕 Bước 2: Chọn Ảnh Trang Phục (Outfit)", "outfit")
        self.btn_bg = self._create_pick_btn("🖼️ Bước 3: Chọn Ảnh Bối Cảnh (Background)", "bg")
        
        layout.addWidget(self.btn_id)
        layout.addWidget(self.btn_outfit)
        layout.addWidget(self.btn_bg)

        layout.addWidget(QLabel("📝 CÂU LỆNH TẠO ẢNH A:"))
        self.input_prompt = QLineEdit("Create a beautiful Vietnamese model based on these refs, 9:16 vertical.")
        layout.addWidget(self.input_prompt)

        self.btn_run = QPushButton("🚀 KHỞI CHẠY QUY TRÌNH (ENGINE: CHATGPT)")
        self.btn_run.setFixedHeight(65)
        self.btn_run.setStyleSheet("background-color: #ff4d6d; color: white; font-size: 14px; font-weight: bold;")
        self.btn_run.clicked.connect(self.start_test)
        layout.addWidget(self.btn_run)

        self.log_view = QTextEdit()
        layout.addWidget(self.log_view)

    def _create_pick_btn(self, text, key):
        btn = QPushButton(text)
        btn.clicked.connect(lambda: self.pick_single(key, btn))
        return btn

    def pick_single(self, key, btn):
        # Mở mặc định tại ổ F: của bạn
        path, _ = QFileDialog.getOpenFileName(self, "Chọn ảnh tham chiếu", "F:/Data_Tool/temmp", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.paths[key] = os.path.normpath(path)
            btn.setText(f"✅ {os.path.basename(path)}")
            btn.setStyleSheet("color: #4CAF50; border: 2px solid #4CAF50; font-weight: bold;")

    def start_test(self):
        if not all(self.paths.values()):
            self.log_view.append("⚠️ Vui lòng chọn đủ 3 ảnh theo thứ tự!")
            return
        
        self.btn_run.setEnabled(False)
        self.log_view.clear()
        self.log_view.append(f"▶️ Đang mở trình duyệt với Profile: google_acc_3...")
        
        # Thư mục lưu kết quả test riêng
        save_path = os.path.join(os.getcwd(), "test_results_images")
        os.makedirs(save_path, exist_ok=True)

        self.worker = TestWorker(
            self.paths["id"], 
            self.paths["outfit"], 
            self.paths["bg"], 
            self.input_prompt.text(), 
            save_path
        )
        self.worker.finished.connect(self.on_worker_done)
        self.worker.start()

    def on_worker_done(self):
        self.btn_run.setEnabled(True)
        self.log_view.append("\n🏁 TIẾN TRÌNH TEST KẾT THÚC.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QuickTestApp()
    window.show()
    sys.exit(app.exec())