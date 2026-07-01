import json
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QPushButton, QListWidget, QLineEdit, QTextEdit, 
                             QLabel, QFrame, QMessageBox)
from PyQt6.QtCore import Qt

class PromptManagerPage(QWidget):
    def __init__(self, config_mgr):
        super().__init__()
        self.mgr = config_mgr
        self.builder = self.mgr.builder
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QHBoxLayout()
        header.addWidget(QLabel("<h2>⚙️ QUẢN LÝ NỘI DUNG AI</h2>"))
        header.addStretch()
        self.btn_save_all = QPushButton("💾 LƯU TOÀN BỘ THAY ĐỔI")
        self.btn_save_all.setObjectName("PrimaryBtn")
        self.btn_save_all.setFixedSize(220, 40)
        self.btn_save_all.clicked.connect(self.save_all_data)
        header.addWidget(self.btn_save_all)
        layout.addLayout(header)

        self.tabs = QTabWidget()
        
        # --- TAB 1: SẢN PHẨM ---
        self.tab_products = QWidget()
        self.init_tab_products()
        self.tabs.addTab(self.tab_products, "👕 Sản phẩm")

        # --- TAB 2: KỊCH BẢN ---
        self.tab_scenarios = QWidget()
        self.init_tab_scenarios()
        self.tabs.addTab(self.tab_scenarios, "🎬 Kịch bản (Scenarios)")

        layout.addWidget(self.tabs)

    def init_tab_products(self):
        layout = QVBoxLayout(self.tab_products)
        self.table_prod = QTableWidget(0, 2)
        self.table_prod.setHorizontalHeaderLabels(["Tên Tiếng Việt", "Tên Tiếng Anh (Gửi AI)"])
        self.table_prod.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        products = self.builder.get_products()
        for vn, en in products.items():
            self.add_product_row(vn, en)

        btn_box = QHBoxLayout()
        btn_add = QPushButton("+ Thêm SP")
        btn_add.clicked.connect(lambda: self.add_product_row("", ""))
        btn_del = QPushButton("- Xóa dòng")
        btn_del.clicked.connect(lambda: self.table_prod.removeRow(self.table_prod.currentRow()))
        btn_box.addWidget(btn_add); btn_box.addWidget(btn_del); btn_box.addStretch()
        
        layout.addLayout(btn_box)
        layout.addWidget(self.table_prod)

    def add_product_row(self, vn, en):
        row = self.table_prod.rowCount()
        self.table_prod.insertRow(row)
        self.table_prod.setItem(row, 0, QTableWidgetItem(str(vn)))
        self.table_prod.setItem(row, 1, QTableWidgetItem(str(en)))

    def init_tab_scenarios(self):
        layout = QHBoxLayout(self.tab_scenarios)
        
        # Left Side: List
        left = QVBoxLayout()
        self.list_scen = QListWidget()
        self.list_scen.setFixedWidth(220)
        self.list_scen.itemClicked.connect(self.load_scenario_details)
        left.addWidget(QLabel("Chọn Kịch bản:"))
        left.addWidget(self.list_scen)
        
        btn_new = QPushButton("+ Kịch bản mới")
        btn_new.clicked.connect(self.prepare_new_scenario)
        left.addWidget(btn_new)
        layout.addLayout(left)

        # Right Side: Form
        self.form = QFrame()
        f_lay = QVBoxLayout(self.form)
        
        self.edit_key = QLineEdit(); self.edit_key.setPlaceholderText("ID (ví dụ: basic_model)")
        self.edit_name = QLineEdit(); self.edit_name.setPlaceholderText("Tên hiển thị...")
        self.edit_img_temp = QTextEdit(); self.edit_img_temp.setPlaceholderText("Image Prompt Template...")
        self.edit_vid_temp = QTextEdit(); self.edit_vid_temp.setPlaceholderText("ChatGPT Video Prompt...")
        
        # NÂNG CẤP BẢNG SHOTS: Thêm cột Target Count và Variants
        self.table_shots = QTableWidget(0, 4)
        self.table_shots.setHorizontalHeaderLabels(["Mã Shot", "Mô tả Shot", "Ảnh AI (Số lượng)", "Biến thể (Video)"])
        self.table_shots.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        f_lay.addWidget(QLabel("Mã ID:")); f_lay.addWidget(self.edit_key)
        f_lay.addWidget(QLabel("Tên kịch bản:")); f_lay.addWidget(self.edit_name)
        f_lay.addWidget(QLabel("Template Tạo Ảnh:")); f_lay.addWidget(self.edit_img_temp)
        f_lay.addWidget(QLabel("Template ChatGPT:")); f_lay.addWidget(self.edit_vid_temp)
        
        s_btns = QHBoxLayout()
        btn_add_s = QPushButton("+ Thêm Shot")
        btn_add_s.clicked.connect(lambda: self.add_shot_row("", "", "2", "1"))
        s_btns.addWidget(btn_add_s); s_btns.addStretch()
        f_lay.addLayout(s_btns)
        f_lay.addWidget(self.table_shots)

        layout.addWidget(self.form)
        self.refresh_scen_list()

    def add_shot_row(self, key, desc, count, var):
        r = self.table_shots.rowCount()
        self.table_shots.insertRow(r)
        self.table_shots.setItem(r, 0, QTableWidgetItem(str(key)))
        self.table_shots.setItem(r, 1, QTableWidgetItem(str(desc)))
        self.table_shots.setItem(r, 2, QTableWidgetItem(str(count)))
        self.table_shots.setItem(r, 3, QTableWidgetItem(str(var)))

    def refresh_scen_list(self):
        self.list_scen.clear()
        for k in self.builder.db.get("scenarios", {}).keys():
            self.list_scen.addItem(k)

    def load_scenario_details(self, item):
        key = item.text()
        data = self.builder.db["scenarios"].get(key, {})
        self.edit_key.setText(key)
        self.edit_key.setReadOnly(True)
        self.edit_name.setText(data.get("display_name", ""))
        self.edit_img_temp.setText(data.get("image_prompt_template", ""))
        self.edit_vid_temp.setText(data.get("chatgpt_video_prompt", ""))
        
        self.table_shots.setRowCount(0)
        shots = data.get("shots", {})
        for s_key, s_val in shots.items():
            # Xử lý cả kiểu cũ (string) và kiểu mới (dict)
            if isinstance(s_val, dict):
                self.add_shot_row(s_key, s_val.get("prompt", ""), s_val.get("target_count", 2), s_val.get("variants", 1))
            else:
                self.add_shot_row(s_key, s_val, "2", "1")

    def prepare_new_scenario(self):
        self.edit_key.clear(); self.edit_key.setReadOnly(False)
        self.edit_name.clear(); self.edit_img_temp.clear(); self.edit_vid_temp.clear()
        self.table_shots.setRowCount(0)

    def save_all_data(self):
        # 1. Thu thập Sản phẩm
        new_prods = {}
        for r in range(self.table_prod.rowCount()):
            vn = self.table_prod.item(r, 0).text().strip()
            en = self.table_prod.item(r, 1).text().strip()
            if vn: new_prods[vn] = en
        
        # 2. Thu thập Kịch bản
        key = self.edit_key.text().strip()
        if key:
            shots_data = {}
            for r in range(self.table_shots.rowCount()):
                sk = self.table_shots.item(r, 0).text().strip()
                sd = self.table_shots.item(r, 1).text().strip()
                sc = self.table_shots.item(r, 2).text().strip()
                sv = self.table_shots.item(r, 3).text().strip()
                if sk:
                    shots_data[sk] = {
                        "prompt": sd,
                        "target_count": int(sc) if sc.isdigit() else 2,
                        "variants": int(sv) if sv.isdigit() else 1
                    }
            
            self.builder.db["scenarios"][key] = {
                "display_name": self.edit_name.text().strip(),
                "image_prompt_template": self.edit_img_temp.toPlainText().strip(),
                "chatgpt_video_prompt": self.edit_vid_temp.toPlainText().strip(),
                "shots": shots_data
            }

        # 3. Lưu xuống file JSON
        self.builder.products = new_prods
        if self.builder.save_all():
            QMessageBox.information(self, "OK", "Đã cập nhật toàn bộ hệ thống JSON!")
            self.refresh_scen_list()