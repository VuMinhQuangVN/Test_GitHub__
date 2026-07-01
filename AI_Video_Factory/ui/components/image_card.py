# # ui/components/image_card.py
# from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QTextEdit, QPushButton, QProgressBar, QApplication, QFileDialog
# from PyQt6.QtGui import QPixmap
# from PyQt6.QtCore import Qt, pyqtSignal
# import os

# class ImageCard(QFrame):
#     # Signal để báo cho MainWindow biết card này muốn tự xóa mình
#     remove_requested = pyqtSignal(QFrame)

#     def __init__(self, paths=None):
#         super().__init__()
#         if paths is None:
#             self.img_paths = ["", ""]
#         elif isinstance(paths, str):
#             self.img_paths = paths.split("|")
#         else:
#             self.img_paths = paths
            
#         self.video_path = None
#         self.setObjectName("ImageCard")
#         self.setFixedHeight(350)
        
#         self.main_layout = QHBoxLayout(self)
#         self.main_layout.setContentsMargins(10, 10, 10, 10)
#         self.main_layout.setSpacing(15)
        
#         # --- BÊN TRÁI: HIỂN THỊ ẢNH (ẢNH CƠ) ---
#         self.media_container = QFrame()
#         self.media_container.setFixedWidth(240)
#         self.media_layout = QVBoxLayout(self.media_container)
        
#         self.img_labels = []
#         for i in range(2):
#             unit_box = QVBoxLayout()
#             lbl = QLabel()
#             lbl.setFixedSize(220, 120)
#             lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
#             lbl.setStyleSheet("background: #000; border-radius: 4px; border: 1px solid #252a3d;")
            
#             btn_pick = QPushButton(f"Chọn ảnh {'Đầu' if i==0 else 'Cuối'}")
#             btn_pick.setStyleSheet("font-size: 10px; height: 20px;")
#             btn_pick.clicked.connect(lambda chk, idx=i: self.manual_pick_image(idx))
            
#             unit_box.addWidget(lbl)
#             unit_box.addWidget(btn_pick)
#             self.media_layout.addLayout(unit_box)
#             self.img_labels.append(lbl)
#             self.update_preview(i)

#         self.pbar = QProgressBar()
#         self.pbar.setVisible(False)
#         self.media_layout.addWidget(self.pbar)
        
#         # --- BÊN PHẢI: NỘI DUNG & ĐIỀU KHIỂN ---
#         self.right_panel = QVBoxLayout()
        
#         # Header (Status + Nút Xóa nhanh)
#         header_layout = QHBoxLayout()
#         self.status_label = QLabel("⏳ Đang chuẩn bị kịch bản...")
#         self.status_label.setStyleSheet("color: #ff4d6d; font-weight: bold; font-size: 12px;")
        
#         self.btn_remove = QPushButton("🗑️") # Nút xóa Card
#         self.btn_remove.setFixedSize(30, 30)
#         self.btn_remove.setToolTip("Xóa Card này")
#         self.btn_remove.setStyleSheet("background: #333; border-radius: 15px; color: #fff;")
#         self.btn_remove.clicked.connect(self.remove_self)
        
#         header_layout.addWidget(self.status_label)
#         header_layout.addStretch()
#         header_layout.addWidget(self.btn_remove)
#         self.right_panel.addLayout(header_layout)
        
#         # Ô nhập Prompt
#         self.prompt_display = QTextEdit()
#         self.prompt_display.setStyleSheet("background-color: #0f111a; color: #eee; border-radius: 6px; padding: 5px;")
#         self.right_panel.addWidget(self.prompt_display)
        
#         # Dòng nút bấm dưới cùng
#         self.footer_layout = QHBoxLayout()
#         self.btn_copy = QPushButton("📋 Copy")
#         self.btn_copy.setFixedWidth(80)
#         self.btn_copy.clicked.connect(self.copy_to_clipboard)
        
#         self.btn_create_video = QPushButton("🎬 TẠO VIDEO")
#         self.btn_create_video.setObjectName("PrimaryBtn")
#         self.btn_create_video.setMinimumWidth(120)
        
#         self.btn_open_video = QPushButton("📂 Mở Video")
#         self.btn_open_video.setVisible(False) # Ẩn khi chưa có video
#         self.btn_open_video.setStyleSheet("background: #4CAF50; color: white; font-weight: bold;")
#         self.btn_open_video.clicked.connect(self.open_video_folder)

#         self.footer_layout.addWidget(self.btn_copy)
#         self.footer_layout.addStretch()
#         self.footer_layout.addWidget(self.btn_open_video)
#         self.footer_layout.addWidget(self.btn_create_video)
#         self.right_panel.addLayout(self.footer_layout)
        
#         self.main_layout.addWidget(self.media_container, 4)
#         self.main_layout.addLayout(self.right_panel, 6)

#     def manual_pick_image(self, index):
#         path, _ = QFileDialog.getOpenFileName(self, "Chọn ảnh", "", "Images (*.png *.jpg *.jpeg)")
#         if path:
#             self.img_paths[index] = os.path.normpath(path)
#             self.update_preview(index)

#     def update_preview(self, index):
#         path = self.img_paths[index]
#         if path and os.path.exists(path):
#             pix = QPixmap(path)
#             if not pix.isNull():
#                 self.img_labels[index].setPixmap(pix.scaled(220, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
#                 self.img_labels[index].setText("")
#             else: self.img_labels[index].setText("Lỗi")
#         else:
#             self.img_labels[index].setPixmap(QPixmap())
#             self.img_labels[index].setText("Trống")

#     def update_prompts(self, result):
#         if result and 'data' in result:
#             data = result['data']
#             prompt = data.get('prompt', '') if isinstance(data, dict) else data[0].get('prompt', '')
#             self.prompt_display.setText(prompt)
#             self.status_label.setText("✅ Kịch bản sẵn sàng")
#             self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

#     def set_loading(self, text):
#         self.status_label.setText(f"🚀 {text}")
#         self.status_label.setStyleSheet("color: #ffb703; font-weight: bold;")
#         self.pbar.setVisible(True)
#         self.pbar.setRange(0, 0)
#         self.btn_create_video.setEnabled(False)

#     def set_success(self, video_path):
#         """Khi video render xong"""
#         self.video_path = os.path.normpath(video_path)
#         self.pbar.setVisible(False)
#         self.status_label.setText("🎉 VIDEO HOÀN TẤT")
#         self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        
#         # Hiện nút Mở Video, Ẩn nút Tạo Video
#         self.btn_open_video.setVisible(True)
#         self.btn_create_video.setVisible(False)

#     def copy_to_clipboard(self):
#         QApplication.clipboard().setText(self.prompt_display.toPlainText())
#         self.btn_copy.setText("✔ Copied")

#     def open_video_folder(self):
#         """Mở thư mục và trỏ đúng vào file video"""
#         if self.video_path and os.path.exists(self.video_path):
#             # Sử dụng lệnh chuẩn của Windows để highlight file
#             cmd = f'explorer /select,"{self.video_path}"'
#             os.system(cmd)
#         else:
#             self.status_label.setText("❌ Không tìm thấy file video!")
#             self.status_label.setStyleSheet("color: red;")

#     def remove_self(self):
#         """Xóa card khỏi giao diện"""
#         self.setParent(None)
#         self.deleteLater()
# ui/components/image_card.py
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QVBoxLayout, QLabel, 
                             QTextEdit, QPushButton, QProgressBar, QApplication, 
                             QFileDialog, QScrollArea, QWidget)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, pyqtSignal
import os

class ImageCard(QFrame):
    # Signal để báo cho MainWindow biết card này muốn tự xóa mình
    remove_requested = pyqtSignal(QFrame)

    def __init__(self, paths=None):
        super().__init__()
        
        # --- CHUẨN HÓA ĐẦU VÀO LINH HOẠT ---
        if not paths:
            self.img_paths = [""] # Mặc định 1 ô trống nếu không truyền gì
        elif isinstance(paths, str):
            self.img_paths = [p for p in paths.split("|") if p.strip()]
        else:
            self.img_paths = list(paths) # Đảm bảo copy thành list an toàn
            
        self.video_path = None
        self.setObjectName("ImageCard")
        self.setMinimumHeight(350) # Đổi thành Minimum để linh hoạt co giãn
        
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(15)
        
        # ==========================================================
        # BÊN TRÁI: HIỂN THỊ ẢNH (DÙNG SCROLL AREA ĐỂ KHÔNG BỊ VỠ LAYOUT)
        # ==========================================================
        self.scroll_area = QScrollArea()
        self.scroll_area.setFixedWidth(260)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.media_container = QWidget()
        self.media_container.setStyleSheet("background: transparent;")
        self.media_layout = QVBoxLayout(self.media_container)
        self.media_layout.setContentsMargins(0, 0, 10, 0) # Chừa lề cho thanh cuộn
        
        self.img_labels = []
        
        # TẠO Ô ẢNH ĐỘNG THEO SỐ LƯỢNG TRUYỀN VÀO
        for i in range(len(self.img_paths)):
            unit_box = QVBoxLayout()
            
            # Label tiêu đề nhỏ (Ví dụ: Ảnh 1 {IMG_1})
            lbl_title = QLabel(f"📸 Ảnh {i+1} {{IMG_{i+1}}}")
            lbl_title.setStyleSheet("color: #888; font-size: 11px; font-weight: bold;")
            
            lbl_img = QLabel()
            lbl_img.setFixedSize(220, 120)
            lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_img.setStyleSheet("background: #000; border-radius: 4px; border: 1px solid #252a3d;")
            
            btn_pick = QPushButton(f"Đổi ảnh {i+1}")
            btn_pick.setStyleSheet("font-size: 10px; height: 20px; background: #333; color: white;")
            btn_pick.clicked.connect(lambda chk, idx=i: self.manual_pick_image(idx))
            
            unit_box.addWidget(lbl_title)
            unit_box.addWidget(lbl_img)
            unit_box.addWidget(btn_pick)
            self.media_layout.addLayout(unit_box)
            self.img_labels.append(lbl_img)
            
            self.update_preview(i)

        self.media_layout.addStretch() # Đẩy các ảnh lên trên cùng
        self.scroll_area.setWidget(self.media_container)
        
        # ==========================================================
        # BÊN PHẢI: NỘI DUNG & ĐIỀU KHIỂN (Giữ nguyên form cũ)
        # ==========================================================
        self.right_panel = QVBoxLayout()
        
        # Header (Status + Nút Xóa nhanh)
        header_layout = QHBoxLayout()
        self.status_label = QLabel("⏳ Đang chờ chạy...")
        self.status_label.setStyleSheet("color: #ff4d6d; font-weight: bold; font-size: 12px;")
        
        self.btn_remove = QPushButton("🗑️") 
        self.btn_remove.setFixedSize(30, 30)
        self.btn_remove.setToolTip("Xóa Card này")
        self.btn_remove.setStyleSheet("background: #333; border-radius: 15px; color: #fff;")
        self.btn_remove.clicked.connect(self.remove_self)
        
        header_layout.addWidget(self.status_label)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_remove)
        self.right_panel.addLayout(header_layout)
        
        # Thanh Tiến độ
        self.pbar = QProgressBar()
        self.pbar.setVisible(False)
        self.right_panel.addWidget(self.pbar)
        
        # Ô nhập Prompt
        self.prompt_display = QTextEdit()
        self.prompt_display.setStyleSheet("background-color: #0f111a; color: #eee; border-radius: 6px; padding: 5px; font-size: 13px;")
        self.right_panel.addWidget(self.prompt_display)
        
        # Dòng nút bấm dưới cùng
        self.footer_layout = QHBoxLayout()
        self.btn_copy = QPushButton("📋 Copy")
        self.btn_copy.setFixedWidth(80)
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        
        self.btn_create_video = QPushButton("🎬 TẠO VIDEO")
        self.btn_create_video.setObjectName("PrimaryBtn")
        self.btn_create_video.setMinimumWidth(120)
        
        self.btn_open_video = QPushButton("📂 Mở Video")
        self.btn_open_video.setVisible(False) 
        self.btn_open_video.setStyleSheet("background: #4CAF50; color: white; font-weight: bold;")
        self.btn_open_video.clicked.connect(self.open_video_folder)

        self.footer_layout.addWidget(self.btn_copy)
        self.footer_layout.addStretch()
        self.footer_layout.addWidget(self.btn_open_video)
        self.footer_layout.addWidget(self.btn_create_video)
        self.right_panel.addLayout(self.footer_layout)
        
        # Gắn vào layout chính
        self.main_layout.addWidget(self.scroll_area, 3) # Panel ảnh chiếm 3 phần
        self.main_layout.addLayout(self.right_panel, 7) # Panel Text chiếm 7 phần

    # ==========================================================
    # CÁC HÀM XỬ LÝ (Giữ nguyên logic cực tốt của bạn)
    # ==========================================================
    def manual_pick_image(self, index):
        path, _ = QFileDialog.getOpenFileName(self, f"Chọn ảnh {index+1}", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if path:
            self.img_paths[index] = os.path.normpath(path)
            self.update_preview(index)

    def update_preview(self, index):
        path = self.img_paths[index]
        if path and os.path.exists(path):
            pix = QPixmap(path)
            if not pix.isNull():
                self.img_labels[index].setPixmap(pix.scaled(220, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                self.img_labels[index].setText("")
            else: self.img_labels[index].setText("Lỗi định dạng")
        else:
            self.img_labels[index].setPixmap(QPixmap())
            self.img_labels[index].setText("Trống")

    def update_prompts(self, result):
        if result and 'data' in result:
            data = result['data']
            prompt = data.get('prompt', '') if isinstance(data, dict) else data[0].get('prompt', '')
            self.prompt_display.setText(prompt)
            self.status_label.setText("✅ Kịch bản sẵn sàng")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def set_loading(self, text):
        self.status_label.setText(f"🚀 {text}")
        self.status_label.setStyleSheet("color: #ffb703; font-weight: bold;")
        self.pbar.setVisible(True)
        self.pbar.setRange(0, 0)
        self.btn_create_video.setEnabled(False)

    def set_success(self, video_path):
        self.video_path = os.path.normpath(video_path)
        self.pbar.setVisible(False)
        self.status_label.setText("🎉 VIDEO HOÀN TẤT")
        self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        
        self.btn_open_video.setVisible(True)
        self.btn_create_video.setVisible(False)

    def copy_to_clipboard(self):
        QApplication.clipboard().setText(self.prompt_display.toPlainText())
        self.btn_copy.setText("✔ Copied")

    def open_video_folder(self):
        if self.video_path and os.path.exists(self.video_path):
            cmd = f'explorer /select,"{self.video_path}"'
            os.system(cmd)
        else:
            self.status_label.setText("❌ Không tìm thấy file video!")
            self.status_label.setStyleSheet("color: red;")

    def remove_self(self):
        self.setParent(None)
        self.deleteLater()