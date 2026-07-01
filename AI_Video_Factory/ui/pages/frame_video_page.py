# ui/pages/frame_video_page.py
import os, json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QScrollArea, QFrame, QLabel, QFileDialog)
from PyQt6.QtCore import pyqtSignal, Qt
from ui.components.image_card import ImageCard

class FrameVideoPage(QWidget):
    # Tín hiệu này MainWindow sẽ hứng để chạy hàm start_factory_queue
    start_all_production = pyqtSignal()

    def __init__(self, mgr):
        super().__init__()
        self.mgr = mgr
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar chuyên nghiệp
        toolbar = QFrame()
        toolbar.setStyleSheet("background: #161926; border-radius: 10px;")
        t_layout = QHBoxLayout(toolbar)
        
        self.btn_add_manual = QPushButton("➕ Thêm Card thủ công")
        self.btn_import_imgs = QPushButton("🖼️ Quét Thư mục")
        self.btn_factory_start = QPushButton("🚀 SẢN XUẤT HÀNG LOẠT")
        self.btn_factory_start.setObjectName("PrimaryBtn")
        
        # Kết nối sự kiện
        self.btn_add_manual.clicked.connect(self.add_manual_card)
        self.btn_import_imgs.clicked.connect(self.import_folder)
        # MainWindow sẽ lo việc quét grid và gán mode="frames" khi nhận signal này
        self.btn_factory_start.clicked.connect(lambda: self.start_all_production.emit())

        t_layout.addWidget(self.btn_add_manual)
        t_layout.addWidget(self.btn_import_imgs)
        t_layout.addStretch()
        t_layout.addWidget(self.btn_factory_start)
        layout.addWidget(toolbar)

        # Danh sách sản xuất
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.res_widget = QWidget()
        self.res_grid = QVBoxLayout(self.res_widget)
        self.res_grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.res_widget)
        layout.addWidget(self.scroll)

    def add_manual_card(self):
        """Cho phép người dùng tự nạp 1 card trắng để chọn ảnh và nhập prompt thủ công"""
        new_card = ImageCard(paths=None) 
        
        # ĐỒNG BỘ: Truyền thêm mode="frames" khi click tạo lẻ
        new_card.btn_create_video.clicked.connect(
            lambda: self.mgr.main_window.add_to_video_queue(
                new_card.img_paths, 
                " ".join(new_card.prompt_display.toPlainText().split()),
                mode="frames" # <--- THÊM ĐỂ ĐỒNG BỘ
            )
        )
        self.add_production_card(new_card)

    def import_folder(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Chọn thư mục chứa ảnh")
        if dir_path:
            # Chỉ lấy file ảnh
            files = [os.path.join(dir_path, f) for f in os.listdir(dir_path) if f.lower().endswith(('.jpg', '.png'))]
            
            # Quét theo cặp 2 ảnh
            for i in range(0, len(files), 2):
                if i + 1 < len(files):
                    card = ImageCard([files[i], files[i+1]])
                    
                    # ĐỒNG BỘ: Truyền thêm mode="frames" khi click tạo lẻ
                    card.btn_create_video.clicked.connect(
                        lambda c=card: self.mgr.main_window.add_to_video_queue(
                            c.img_paths, 
                            " ".join(c.prompt_display.toPlainText().split()),
                            mode="frames" # <--- THÊM ĐỂ ĐỒNG BỘ
                        )
                    )
                    self.add_production_card(card)

    def add_production_card(self, card):
        self.res_grid.addWidget(card)