# -*- coding: utf-8 -*-
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QTextEdit, QGroupBox, 
                             QScrollArea, QLineEdit)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QDragEnterEvent, QDropEvent

# Import bộ xử lý Logic từ thư mục core
from core.text_video_controller import TextVideoController

# =======================================================
# WIDGET CUSTOM: Ô KÉO THẢ ẢNH (DRAG & DROP)
# =======================================================
class DropImageLabel(QLabel):
    image_changed = pyqtSignal(str) 

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.current_path = ""
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_default_style()

    def set_default_style(self):
        self.setText(f"📥 Kéo thả ảnh vào đây\n\n[{self.title}]")
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #555;
                border-radius: 8px;
                background-color: #1e1e2e;
                color: #aaa;
                font-weight: bold;
            }
            QLabel:hover { border: 2px dashed #4CAF50; background-color: #2a2a3f; }
        """)

    def set_image(self, path):
        if os.path.exists(path):
            self.current_path = os.path.normpath(path)
            pixmap = QPixmap(self.current_path).scaled(
                200, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            self.setPixmap(pixmap)
            self.setStyleSheet("QLabel { border: 2px solid #4CAF50; border-radius: 8px; }")
            self.image_changed.emit(self.current_path)
        else:
            self.clear_image()

    def clear_image(self):
        self.current_path = ""
        self.set_default_style()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("QLabel { border: 2px dashed #00BCD4; background-color: #2a2a3f; }")

    def dragLeaveEvent(self, event):
        if not self.current_path: self.set_default_style()
        else: self.setStyleSheet("QLabel { border: 2px solid #4CAF50; border-radius: 8px; }")

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                self.set_image(file_path)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            from PyQt6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getOpenFileName(self, f"Chọn ảnh cho {self.title}", "", "Images (*.png *.jpg *.jpeg *.webp)")
            if file_path:
                self.set_image(file_path)

# =======================================================
# PAGE CHÍNH: TEXT TO VIDEO (CHỈ CHỨA GIAO DIỆN)
# =======================================================
class TextVideoPage(QWidget):
    def __init__(self, config_manager):
        super().__init__()
        self.mgr = config_manager
        self.drop_zones = []

        self.init_ui()
        
        # KHỞI TẠO BỘ ĐIỀU KHIỂN LOGIC (Nạp Controller ở cuối cùng để kết nối tín hiệu)
        self.controller = TextVideoController(self, self.mgr)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        # --- KHU VỰC 1: TOP BAR (QUẢN LÝ PRESET) ---
        top_bar = QHBoxLayout()
        self.cb_presets = QComboBox()
        self.cb_presets.setMinimumHeight(35)
        self.cb_presets.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.btn_save_preset = QPushButton("💾 Lưu thành Combo")
        self.btn_save_preset.setMinimumHeight(35)
        self.btn_save_preset.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")

        self.btn_del_preset = QPushButton("🗑 Xóa Combo")
        self.btn_del_preset.setMinimumHeight(35)
        self.btn_del_preset.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")

        top_bar.addWidget(QLabel("📦 Combo Sản Phẩm:"))
        top_bar.addWidget(self.cb_presets, 1) 
        top_bar.addWidget(self.btn_save_preset)
        top_bar.addWidget(self.btn_del_preset)
        main_layout.addLayout(top_bar)

        # --- KHU VỰC 2: INPUT ---
        input_layout = QHBoxLayout()
        
        left_panel = QGroupBox("📸 Hình ảnh Tham chiếu")
        left_layout_main = QVBoxLayout(left_panel)
        scroll_img = QScrollArea()
        scroll_img.setWidgetResizable(True)
        scroll_img.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.img_container = QWidget()
        self.img_layout = QVBoxLayout(self.img_container)
        self.img_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_img.setWidget(self.img_container)
        left_layout_main.addWidget(scroll_img)
        
        right_panel = QGroupBox("📝 Thông tin & Kịch bản")
        right_layout = QVBoxLayout(right_panel)

        self.cb_scenarios = QComboBox()
        self.cb_scenarios.setMinimumHeight(35)

        # COMBOBOX CHỌN NHANH MÔ TẢ MẪU
        self.cb_desc_templates = QComboBox()
        self.cb_desc_templates.setMinimumHeight(35)

        # Ô NHẬP LỜI THOẠI VIRAL THAM KHẢO
        self.txt_viral_transcript = QTextEdit()
        self.txt_viral_transcript.setPlaceholderText("Dán lời thoại của video triệu view vào đây để bắt AI học hỏi và biến tấu phong cách nói (Không bắt buộc)...")
        self.txt_viral_transcript.setStyleSheet("font-size: 13px; padding: 10px;")
        self.txt_viral_transcript.setMaximumHeight(80) 
        
        self.txt_description = QTextEdit()
        self.txt_description.setPlaceholderText("Ví dụ: Áo sơ mi lụa trắng công sở, mặc mùa thu, sang trọng, thanh lịch...")
        self.txt_description.setStyleSheet("font-size: 14px; padding: 10px;")

        self.btn_generate = QPushButton("🤖 SINH KỊCH BẢN BẰNG CHATGPT")
        self.btn_generate.setMinimumHeight(45)
        self.btn_generate.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; font-size: 15px;")
        
        right_layout.addWidget(QLabel("🎭 Chọn phong cách:"))
        right_layout.addWidget(self.cb_scenarios)
        
        # Chọn Mô tả mẫu có thêm nút Lưu bên cạnh
        right_layout.addWidget(QLabel("📝 Chọn Mô tả mẫu (Để điền nhanh):"))
        desc_tpl_layout = QHBoxLayout()
        self.cb_desc_templates = QComboBox()
        self.cb_desc_templates.setMinimumHeight(35)
        
        self.btn_save_desc_template = QPushButton("💾 Lưu Mẫu")
        self.btn_save_desc_template.setMinimumHeight(35)
        self.btn_save_desc_template.setStyleSheet("background-color: #00BCD4; color: white; font-weight: bold;")
        
        desc_tpl_layout.addWidget(self.cb_desc_templates, 1) 
        desc_tpl_layout.addWidget(self.btn_save_desc_template)
        right_layout.addLayout(desc_tpl_layout) 

        # Add ô nhập lời thoại mẫu vào Layout hiển thị
        right_layout.addWidget(QLabel("🔥 Lời thoại mẫu / Viral Transcript (Tùy chọn):"))
        right_layout.addWidget(self.txt_viral_transcript)
        
        right_layout.addWidget(QLabel("👗 Mô tả chi tiết sản phẩm (Mớm cho AI):"))
        right_layout.addWidget(self.txt_description)
        right_layout.addWidget(self.btn_generate)

        input_layout.addWidget(left_panel, 3)  
        input_layout.addWidget(right_panel, 7) 
        main_layout.addLayout(input_layout, 1)

        # --- KHU VỰC 3: KẾT QUẢ PROMPT & CẤU HÌNH OUTPUT ---
        result_panel = QGroupBox("🎬 Kết quả Kịch bản & Hàng đợi Render")
        result_main_layout = QVBoxLayout(result_panel)

        self.scroll_results = QScrollArea()
        self.scroll_results.setWidgetResizable(True)
        self.scroll_results.setStyleSheet("QScrollArea { border: 1px solid #333; background: #0b0d14; }")
        self.result_container = QWidget()
        self.result_layout = QVBoxLayout(self.result_container)
        self.result_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.result_layout.setSpacing(15)
        self.scroll_results.setWidget(self.result_container)
        result_main_layout.addWidget(self.scroll_results)

        save_layout = QHBoxLayout()
        self.txt_save_dir = QLineEdit()
        self.txt_save_dir.setPlaceholderText("Chưa chọn thư mục lưu video. Bấm nút bên cạnh 👉")
        self.txt_save_dir.setReadOnly(True)
        self.txt_save_dir.setStyleSheet("background: #1e1e2e; color: #fff; padding: 8px; font-size: 13px; border-radius: 4px;")
        
        self.btn_browse_dir = QPushButton("📁 Chọn Thư Mục Lưu Video")
        self.btn_browse_dir.setStyleSheet("background-color: #5C6BC0; color: white; font-weight: bold; padding: 8px;")
        
        save_layout.addWidget(QLabel("💾 Output:"))
        save_layout.addWidget(self.txt_save_dir, 1)
        save_layout.addWidget(self.btn_browse_dir)
        result_main_layout.addLayout(save_layout)

        self.btn_render_all = QPushButton("🚀 CHẠY RENDER TẤT CẢ VÀO HÀNG ĐỢI")
        self.btn_render_all.setMinimumHeight(45)
        self.btn_render_all.setStyleSheet("background-color: #9C27B0; color: white; font-weight: bold; font-size: 15px;")
        result_main_layout.addWidget(self.btn_render_all)

        main_layout.addWidget(result_panel, 2)

    # =======================================================
    # UI UTILITIES (CHỈ THAO TÁC WIDGET)
    # =======================================================
    def clear_result_layout(self):
        """Hàm dọn dẹp các widget cũ trên giao diện"""
        for i in reversed(range(self.result_layout.count())): 
            item = self.result_layout.itemAt(i)
            if item:
                w = item.widget()
                if w:
                    w.setParent(None)
                    w.deleteLater()

    def build_image_drop_zones(self, num_images):
        """Dựng động các ô kéo thả ảnh"""
        for dz in self.drop_zones:
            self.img_layout.removeWidget(dz)
            dz.deleteLater()
        self.drop_zones.clear()

        for i in range(num_images):
            title = f"{{IMG_{i+1}}}"
            if i == 0: title += " - Sản Phẩm/Mẫu"
            elif i == 1: title += " - Background"
            dz = DropImageLabel(title)
            dz.setMinimumHeight(120)
            self.img_layout.addWidget(dz)
            self.drop_zones.append(dz)