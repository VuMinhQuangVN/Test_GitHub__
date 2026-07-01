# settings_page.py
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QScrollArea, QLineEdit, QMessageBox)
from PyQt6.QtCore import Qt
from ui.workers.login_worker import LoginWorker

class SettingsPage(QWidget):
    def __init__(self, config_manager):
        super().__init__()
        self.mgr = config_manager
        self.active_login_threads = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- PHẦN 1: THÊM TÀI KHOẢN MỚI ---
        add_acc_box = QFrame()
        add_acc_box.setObjectName("InputCard")
        add_layout = QHBoxLayout(add_acc_box)
        
        self.new_acc_input = QLineEdit()
        self.new_acc_input.setPlaceholderText("Nhập tên nick mới (VD: google_acc_8)")
        
        btn_add = QPushButton("➕ Tạo Profile Mới")
        btn_add.setObjectName("PrimaryBtn")
        btn_add.setFixedWidth(150)
        btn_add.clicked.connect(self.create_new_profile)
        
        add_layout.addWidget(QLabel("Thêm Nick:"))
        add_layout.addWidget(self.new_acc_input)
        add_layout.addWidget(btn_add)
        layout.addWidget(add_acc_box)

        # --- PHẦN 2: DANH SÁCH QUẢN LÝ ---
        layout.addWidget(QLabel("<b>DANH SÁCH TÀI KHOẢN (Bấm để đăng nhập):</b>"))
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.list_container)
        
        layout.addWidget(self.scroll)
        self.refresh_acc_list()

    def refresh_acc_list(self):
        """Xóa sạch danh sách cũ và quét lại folder profiles/"""
        # Xóa các widget cũ trong list
        for i in reversed(range(self.list_layout.count())): 
            self.list_layout.itemAt(i).widget().setParent(None)

        # Lấy danh sách từ folder thực tế
        profiles = self.mgr.get_all_profiles()
        
        for p_name in profiles:
            item = QFrame()
            item.setStyleSheet("background: #161926; border-radius: 8px; margin: 2px;")
            item_layout = QHBoxLayout(item)
            
            icon = "⭐" if "chrome_auto_profile" in p_name else "👤"
            name_lbl = QLabel(f"{icon} {p_name}")
            name_lbl.setStyleSheet("color: white; font-weight: bold;")
            
            btn_login = QPushButton("🔓 Mở Chrome Đăng Nhập")
            btn_login.setFixedWidth(180)
            btn_login.setStyleSheet("background: #252a3d; color: #a0a5b8; border: 1px solid #3e445e;")
            btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
            
            # Kết nối click: Mở trình duyệt cho profile này
            btn_login.clicked.connect(lambda checked, name=p_name: self.open_login_browser(name))
            
            item_layout.addWidget(name_lbl)
            item_layout.addStretch()
            item_layout.addWidget(btn_login)
            
            self.list_layout.addWidget(item)

    def create_new_profile(self):
        name = self.new_acc_input.text().strip()
        if not name: return
        
        # Tạo folder thực tế trong thư mục profiles/
        target_path = os.path.join(os.getcwd(), "profiles", name)
        if os.path.exists(target_path):
            QMessageBox.warning(self, "Lỗi", "Tên nick này đã tồn tại!")
            return
            
        os.makedirs(target_path, exist_ok=True)
        self.new_acc_input.clear()
        self.refresh_acc_list()
        QMessageBox.information(self, "Thành công", f"Đã tạo profile {name}. Hãy bấm đăng nhập.")

    def open_login_browser(self, p_name):
        worker = LoginWorker(p_name)
        worker.finished.connect(lambda: print(f"✅ Đã đóng trình duyệt {p_name}"))
        worker.start()
        self.active_login_threads.append(worker)