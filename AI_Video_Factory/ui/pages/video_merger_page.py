import os
import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QFileDialog, QFrame, 
                             QProgressBar, QMessageBox, QComboBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from engines.video_editor import VideoEditorEngine

# Worker để chạy MoviePy ngầm, tránh treo giao diện
class RenderWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, engine, edl_json, base_folder, output_path, sticker):
        super().__init__()
        self.engine = engine
        self.edl_json = edl_json
        self.base_folder = base_folder
        self.output_path = output_path
        self.sticker = sticker

    def run(self):
        try:
            result = self.engine.assemble_fashion_story(
                self.edl_json, self.base_folder, self.output_path, self.sticker
            )
            if result:
                self.finished.emit(result)
            else:
                self.error.emit("Render thất bại không rõ nguyên nhân.")
        except Exception as e:
            self.error.emit(str(e))

class VideoMergerPage(QWidget):
    def __init__(self, config_mgr):
        super().__init__()
        self.mgr = config_mgr
        self.engine = VideoEditorEngine()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- PHẦN 1: CÀI ĐẶT NGUỒN ---
        input_card = QFrame()
        input_card.setObjectName("InputCard")
        grid = QVBoxLayout(input_card)

        # Chọn thư mục chứa các clip thô
        folder_lay = QHBoxLayout()
        self.path_edit = QTextEdit()
        self.path_edit.setFixedHeight(35)
        self.path_edit.setPlaceholderText("Đường dẫn thư mục chứa video thô (videos/)...")
        btn_browse = QPushButton("📁 Chọn Thư Mục")
        btn_browse.clicked.connect(self.browse_folder)
        folder_lay.addWidget(self.path_edit)
        folder_lay.addWidget(btn_browse)
        
        # Chọn nhãn dán che Logo
        sticker_lay = QHBoxLayout()
        self.sticker_edit = QTextEdit()
        self.sticker_edit.setFixedHeight(35)
        self.sticker_edit.setPlaceholderText("Đường dẫn file nhãn dán .png (Che logo Veo)...")
        btn_sticker = QPushButton("🖼️ Chọn Nhãn Dán")
        btn_sticker.clicked.connect(self.browse_sticker)
        sticker_lay.addWidget(self.sticker_edit)
        sticker_lay.addWidget(btn_sticker)

        grid.addLayout(folder_lay)
        grid.addLayout(sticker_lay)
        layout.addWidget(input_card)

        # --- PHẦN 2: SOẠN THẢO EDL (JSON) ---
        layout.addWidget(QLabel("<b>📜 Kịch bản biên tập (EDL JSON):</b>"))
        self.edl_input = QTextEdit()
        self.edl_input.setPlaceholderText("Dán mã JSON kịch bản biên tập từ Gemini vào đây...")
        self.edl_input.setStyleSheet("background-color: #0f111a; color: #4CAF50; font-family: Consolas;")
        layout.addWidget(self.edl_input)

        # --- PHẦN 3: ĐIỀU KHIỂN RENDER ---
        ctl_lay = QHBoxLayout()
        
        # Dropdown chọn chế độ (Lõi A hoặc Lõi B)
        self.cb_mode = QComboBox()
        self.cb_mode.addItems(["Fashion Story (Ghép nhiều shot)", "Batch Showcase (1 clip -> 12s)"])
        self.cb_mode.setFixedWidth(250)
        
        self.btn_render = QPushButton("🚀 BẮT ĐẦU BIÊN TẬP & XUẤT VIDEO")
        self.btn_render.setObjectName("PrimaryBtn")
        self.btn_render.setFixedHeight(50)
        self.btn_render.clicked.connect(self.start_render)

        ctl_lay.addWidget(self.cb_mode)
        ctl_lay.addWidget(self.btn_render)
        layout.addLayout(ctl_lay)

        # Tiến độ
        self.pbar = QProgressBar()
        self.pbar.setVisible(False)
        layout.addWidget(self.pbar)

    def browse_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Chọn thư mục chứa video")
        if path: self.path_edit.setText(os.path.normpath(path))

    def browse_sticker(self):
        path, _ = QFileDialog.getOpenFileName(self, "Chọn file nhãn dán", "", "Images (*.png)")
        if path: self.sticker_edit.setText(os.path.normpath(path))

    def start_render(self):
        # 1. Validate
        base_folder = self.path_edit.toPlainText().strip()
        try:
            edl_data = json.loads(self.edl_input.toPlainText().strip())
        except:
            QMessageBox.critical(self, "Lỗi", "Mã JSON kịch bản không hợp lệ!")
            return

        if not os.path.exists(base_folder):
            QMessageBox.critical(self, "Lỗi", "Thư mục video không tồn tại!")
            return

        # 2. Chuẩn bị đường dẫn đầu ra
        output_name = f"Final_Fashion_{os.path.basename(base_folder)}.mp4"
        output_path = os.path.join(base_folder, output_name)

        # 3. Chạy Worker
        self.btn_render.setEnabled(False)
        self.pbar.setVisible(True)
        self.pbar.setRange(0, 0) # Chế độ loading

        self.worker = RenderWorker(
            self.engine, edl_data, base_folder, output_path, self.sticker_edit.toPlainText().strip()
        )
        self.worker.finished.connect(self.on_render_success)
        self.worker.error.connect(self.on_render_error)
        self.worker.start()

    def on_render_success(self, path):
        self.btn_render.setEnabled(True)
        self.pbar.setVisible(False)
        QMessageBox.information(self, "Thành công", f"Video đã được xuất tại:\n{path}")
        os.system(f'explorer /select,"{os.path.normpath(path)}"')

    def on_render_error(self, msg):
        self.btn_render.setEnabled(True)
        self.pbar.setVisible(False)
        QMessageBox.critical(self, "Lỗi Render", f"Có lỗi xảy ra: {msg}")