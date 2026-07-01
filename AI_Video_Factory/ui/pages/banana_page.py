# ui/pages/banana_page.py
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QFileDialog, 
                             QFrame, QGridLayout, QScrollArea)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import pyqtSignal, Qt

class BananaPage(QWidget):
    request_generate = pyqtSignal(dict)

    def __init__(self, config_manager):
        super().__init__()
        self.mgr = config_manager
        self.init_ui()
        self.refresh_data()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # --- KHUNG NHẬP LIỆU ---
        input_card = QFrame()
        input_card.setObjectName("InputCard")
        grid = QGridLayout(input_card)
        grid.setSpacing(10)

        # Hàng 0: SKU
        grid.addWidget(QLabel("Mã SKU:"), 0, 0)
        self.sku_box = QComboBox()
        self.sku_box.setEditable(True)
        self.sku_box.currentTextChanged.connect(self.on_sku_changed)
        grid.addWidget(self.sku_box, 0, 1, 1, 2)

        # Hàng 1, 2, 3: Chọn File + Preview
        self.path_model, self.prev_model = self._add_image_row(grid, "👤 Mẫu Gốc:", 1)
        self.path_prod, self.prev_prod = self._add_image_row(grid, "👕 Sản Phẩm:", 2)
        self.path_bg, self.prev_bg = self._add_image_row(grid, "🖼️ Bối Cảnh:", 3)

        # Hàng 4: Cấu hình + Engine Switch
        dropdown_layout = QHBoxLayout()
        self.cb_type = QComboBox()
        dropdown_layout.addWidget(QLabel("Loại đồ:"))
        dropdown_layout.addWidget(self.cb_type, 1)

        self.cb_shot_set = QComboBox()
        dropdown_layout.addWidget(QLabel("Kịch bản:"))
        dropdown_layout.addWidget(self.cb_shot_set, 1)

        # --- NÚT CHỌN ENGINE (MỚI) ---
        self.cb_engine = QComboBox()
        self.cb_engine.addItem("Google Flow (Vừa vẽ vừa hỏi)", "flow_sequential")
        self.cb_engine.addItem("ChatGPT Parallel (Vẽ 3 - Hỏi 1)", "chatgpt_parallel")
        self.cb_engine.setStyleSheet("background-color: #2c3e50; color: #00d1b2; font-weight: bold;")
        dropdown_layout.addWidget(QLabel("Engine:"))
        dropdown_layout.addWidget(self.cb_engine, 1)

        grid.addLayout(dropdown_layout, 4, 0, 1, 4)
        self.main_layout.addWidget(input_card)

        # --- NÚT CHẠY ---
        self.btn_run = QPushButton("🚀 BẮT ĐẦU SẢN XUẤT (ẢNH & PROMPT)")
        self.btn_run.setObjectName("PrimaryBtn")
        self.btn_run.setFixedHeight(50)
        self.btn_run.clicked.connect(self.on_run_clicked)
        self.main_layout.addWidget(self.btn_run)

        # --- GRID KẾT QUẢ ---
        self.main_layout.addWidget(QLabel("<b>📦 TIẾN ĐỘ THỰC HIỆN:</b>"))
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.res_widget = QWidget()
        self.res_grid = QGridLayout(self.res_widget)
        self.res_grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.res_widget)
        self.main_layout.addWidget(self.scroll)

    def _add_image_row(self, grid, label_text, row):
        grid.addWidget(QLabel(label_text), row, 0)
        line_edit = QLineEdit()
        line_edit.setPlaceholderText("Đường dẫn...")
        grid.addWidget(line_edit, row, 1)
        btn = QPushButton("Chọn")
        btn.setFixedWidth(60)
        grid.addWidget(btn, row, 2)
        prev_label = QLabel("Trống")
        prev_label.setFixedSize(80, 50)
        prev_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        prev_label.setStyleSheet("background: #000; border: 1px solid #333; border-radius: 4px; font-size: 9px;")
        grid.addWidget(prev_label, row, 3)
        btn.clicked.connect(lambda: self._pick_image(line_edit, prev_label))
        line_edit.textChanged.connect(lambda text: self._update_preview(prev_label, text))
        return line_edit, prev_label

    def _pick_image(self, line_edit, prev_label):
        path, _ = QFileDialog.getOpenFileName(self, "Chọn ảnh", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if path:
            line_edit.setText(os.path.normpath(path))

    def _update_preview(self, label, path):
        if path and os.path.exists(path):
            pix = QPixmap(path)
            if not pix.isNull():
                label.setPixmap(pix.scaled(label.width(), label.height(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                label.setText("")
        else:
            label.setPixmap(QPixmap()); label.setText("Trống")

    def refresh_data(self):
        self.sku_box.clear()
        self.sku_box.addItems(self.mgr.get_existing_skus())
        builder = self.mgr.builder 
        self.cb_type.clear()
        for vn, en in builder.get_products().items(): self.cb_type.addItem(vn, en)
        self.cb_shot_set.clear()
        for k, v in builder.get_scenarios().items(): self.cb_shot_set.addItem(v, k)

    def on_sku_changed(self, sku):
        meta = self.mgr.get_sku_metadata(sku)
        if meta:
            self.path_model.setText(meta.get("fixed_model_path", ""))
            self.path_prod.setText(meta.get("product_img_path", ""))
            self.path_bg.setText(meta.get("background_path", ""))
            idx = self.cb_type.findText(meta.get("product_type_vn", ""))
            if idx >= 0: self.cb_type.setCurrentIndex(idx)

    def on_run_clicked(self):
        data = {
            "sku": self.sku_box.currentText().strip(),
            "model_path": self.path_model.text().strip(),
            "prod_path": self.path_prod.text().strip(),
            "bg_path": self.path_bg.text().strip(),
            "type_vn": self.cb_type.currentText(),
            "type_en": self.cb_type.currentData(),
            "scenario_key": self.cb_shot_set.currentData(),
            "engine": self.cb_engine.currentData() # Gửi cờ Engine về Worker
        }
        if not data["sku"] or not data["model_path"] or not data["prod_path"]:
            return
        # Xóa grid cũ
        for i in reversed(range(self.res_grid.count())):
            w = self.res_grid.itemAt(i).widget()
            if w: w.setParent(None)
        self.request_generate.emit(data)