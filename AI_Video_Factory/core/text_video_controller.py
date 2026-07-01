# -*- coding: utf-8 -*-
import os
import json
from datetime import datetime
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QInputDialog, QLabel
from PyQt6.QtCore import QObject

# Import Component và Worker
from ui.components.image_card import ImageCard
from ui.workers.chat_worker import ChatGPTWorker

class TextVideoController(QObject):
    def __init__(self, view, config_manager):
        super().__init__()
        self.view = view
        self.mgr = config_manager
        
        # Load các đường dẫn config từ ConfigManager
        self.preset_file = self.mgr.paths.get("comp_presets", "database/prompts/components_presets.json")
        self.local_config_file = self.mgr.paths.get("comp_settings", "database/settings/components_settings.json")
        self.scenario_file = self.mgr.paths.get("comp_scenarios", "database/prompts/components_scenarios.json")
        
        # Đường dẫn tệp Mô tả mẫu
        self.desc_template_file = os.path.join(self.mgr.prompts_dir, "components_descriptions.json")

        self.scenarios_db = {}
        self.desc_templates_db = {}
        self.chat_worker = None

        self.ensure_files_exist()

        # Kết nối sự kiện từ giao diện sang Controller
        self.connect_signals()

        # Thực thi nạp dữ liệu ban đầu
        self.load_scenarios_to_combo()
        self.load_presets_to_combo()
        self.load_desc_templates_to_combo() # Load danh sách mô tả mẫu
        self.load_saved_directory()

    def ensure_files_exist(self):
        os.makedirs(os.path.dirname(self.preset_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.local_config_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.scenario_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.desc_template_file), exist_ok=True)

        if not os.path.exists(self.preset_file):
            with open(self.preset_file, 'w', encoding='utf-8') as f: json.dump({}, f)
            
        if not os.path.exists(self.local_config_file):
            with open(self.local_config_file, 'w', encoding='utf-8') as f: json.dump({"save_dir": ""}, f)

        # Khởi tạo tệp mô tả mẫu trống rỗng để bạn tự cấu hình thủ công
        if not os.path.exists(self.desc_template_file):
            with open(self.desc_template_file, 'w', encoding='utf-8') as f: json.dump({}, f)

    def connect_signals(self):
        """Kết nối các nút bấm và combobox từ View sang xử lý của Controller"""
        self.view.cb_presets.currentIndexChanged.connect(self.on_preset_selected)
        self.view.btn_save_preset.clicked.connect(self.save_current_preset)
        self.view.btn_del_preset.clicked.connect(self.delete_preset)
        self.view.cb_scenarios.currentIndexChanged.connect(self.on_scenario_changed)
        self.view.btn_generate.clicked.connect(self.generate_prompts_with_chatgpt)
        self.view.btn_browse_dir.clicked.connect(self.browse_save_directory)
        self.view.btn_render_all.clicked.connect(self.push_to_render_queue)
        
        # Kết nối sự kiện liên quan đến mô tả mẫu
        self.view.cb_desc_templates.currentIndexChanged.connect(self.on_desc_template_changed)
        self.view.btn_save_desc_template.clicked.connect(self.save_desc_template)

    # =======================================================
    # LOGIC: THƯ VIỆN MÔ TẢ MẪU (DESCRIPTION TEMPLATES)
    # =======================================================
    def load_desc_templates_to_combo(self):
        self.view.cb_desc_templates.blockSignals(True)
        self.view.cb_desc_templates.clear()
        self.view.cb_desc_templates.addItem("[+] Tự gõ mô tả...", "")
        self.desc_templates_db = self.mgr.load_json(self.desc_template_file, {})
        for name, text in self.desc_templates_db.items():
            self.view.cb_desc_templates.addItem(name, text)
        self.view.cb_desc_templates.blockSignals(False)

    def on_desc_template_changed(self, index):
        template_text = self.view.cb_desc_templates.currentData()
        if template_text:
            self.view.txt_description.setText(template_text)

    def save_desc_template(self):
        desc_text = self.view.txt_description.toPlainText().strip()
        if not desc_text:
            QMessageBox.warning(self.view, "Trống", "Vui lòng nhập nội dung mô tả sản phẩm trước khi lưu làm mẫu!")
            return

        name, ok = QInputDialog.getText(self.view, "Lưu Mô Tả Mẫu", "Nhập tên dòng sản phẩm cho mẫu này:\n(Ví dụ: Áo Hoodie, Váy Jean, Áo Gió Nam...) ")
        if ok and name.strip():
            name = name.strip()
            try:
                data = self.mgr.load_json(self.desc_template_file, {})
                data[name] = desc_text
                self.mgr.save_json(self.desc_template_file, data)
                self.load_desc_templates_to_combo()
                self.view.cb_desc_templates.setCurrentText(name)
                QMessageBox.information(self.view, "Thành công", f"Đã lưu mô tả mẫu cho nhóm '{name}' thành công!")
            except Exception as e:
                QMessageBox.critical(self.view, "Lỗi", f"Không thể lưu tệp Mô tả mẫu: {e}")

    # =======================================================
    # LOGIC: QUẢN LÝ KỊCH BẢN (SCENARIOS)
    # =======================================================
    def load_scenarios_to_combo(self):
        self.view.cb_scenarios.blockSignals(True)
        self.view.cb_scenarios.clear()
        self.scenarios_db = self.mgr.load_json("comp_scenarios", {})
        for key, data in self.scenarios_db.items():
            display_name = data.get("name", key)
            self.view.cb_scenarios.addItem(display_name, data)
        self.view.cb_scenarios.blockSignals(False)
        self.on_scenario_changed()

    def on_scenario_changed(self):
        if self.view.cb_presets.currentIndex() > 0: 
            return 
        scenario_data = self.view.cb_scenarios.currentData()
        if scenario_data:
            required_images = scenario_data.get("required_images", 2)
            self.view.build_image_drop_zones(required_images)

    # =======================================================
    # LOGIC: QUẢN LÝ COMBO PRESETS (LƯU/XÓA)
    # =======================================================
    def load_presets_to_combo(self):
        self.view.cb_presets.blockSignals(True)
        self.view.cb_presets.clear()
        self.view.cb_presets.addItem("[+] Nhập tay mới...", "")
        
        # Dùng hàm load_json của ConfigManager (Tự động trả về dict trống {} nếu file lỗi/trống)
        data = self.mgr.load_json("comp_presets", {})
        
        for preset_name in data.keys():
            self.view.cb_presets.addItem(preset_name, preset_name)
            
        self.view.cb_presets.blockSignals(False)

    def on_preset_selected(self, index):
        preset_name = self.view.cb_presets.currentData()
        if not preset_name: 
            self.on_scenario_changed() 
            self.view.txt_description.clear()
            self.view.txt_viral_transcript.clear()
            self.view.cb_desc_templates.setCurrentIndex(0)
            return

        # Dùng hàm load_json của ConfigManager
        data = self.mgr.load_json("comp_presets", {})
        preset_data = data.get(preset_name, {})
        
        saved_scenario = preset_data.get("scenario", "")
        if saved_scenario:
            self.view.cb_scenarios.blockSignals(True)
            self.view.cb_scenarios.setCurrentText(saved_scenario)
            self.view.cb_scenarios.blockSignals(False)

        self.view.txt_description.setText(preset_data.get("description", ""))
        self.view.txt_viral_transcript.setText(preset_data.get("viral_transcript", ""))
        saved_images = preset_data.get("images", [])
        self.view.build_image_drop_zones(max(len(saved_images), 1))
        
        for i, img_path in enumerate(saved_images):
            if i < len(self.view.drop_zones):
                self.view.drop_zones[i].set_image(img_path)

    def save_current_preset(self):
        desc = self.view.txt_description.toPlainText().strip()
        viral_text = self.view.txt_viral_transcript.toPlainText().strip()
        img_paths = [dz.current_path for dz in self.view.drop_zones if dz.current_path]
        scenario_name = self.view.cb_scenarios.currentText()

        if not desc or not img_paths:
            QMessageBox.warning(self.view, "Thiếu thông tin", "Vui lòng nhập ít nhất 1 Ảnh và Mô tả sản phẩm!")
            return

        name, ok = QInputDialog.getText(self.view, "Lưu Combo", "Nhập tên cho Combo sản phẩm này:\n(Ví dụ: Áo Sơ Mi Lụa - Cảnh Cafe)")
        if ok and name.strip():
            name = name.strip()
            try:
                # 1. Đọc an toàn qua ConfigManager
                data = self.mgr.load_json("comp_presets", {})
                
                # 2. Cập nhật dữ liệu mới
                data[name] = {
                    "scenario": scenario_name,
                    "description": desc,
                    "viral_transcript": viral_text,
                    "images": img_paths
                }
                
                # 3. Ghi an toàn qua ConfigManager
                self.mgr.save_json("comp_presets", data)
                
                self.load_presets_to_combo()
                self.view.cb_presets.setCurrentText(name)
                QMessageBox.information(self.view, "Thành công", f"Đã lưu combo '{name}'")
            except Exception as e:
                QMessageBox.critical(self.view, "Lỗi", f"Không thể lưu JSON: {e}")

    def delete_preset(self):
        preset_name = self.view.cb_presets.currentData()
        if not preset_name: return

        reply = QMessageBox.question(self.view, 'Xác nhận xóa', f"Bạn có chắc muốn xóa combo '{preset_name}'?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 1. Đọc an toàn qua ConfigManager
                data = self.mgr.load_json("comp_presets", {})
                
                # 2. Xóa dữ liệu
                if preset_name in data:
                    del data[preset_name]
                    
                # 3. Ghi an toàn qua ConfigManager
                self.mgr.save_json("comp_presets", data)
                
                self.load_presets_to_combo()
            except Exception as e:
                QMessageBox.critical(self.view, "Lỗi", f"Không thể xóa JSON: {e}")

    # =======================================================
    # LOGIC: THƯ MỤC XUẤT VIDEO (OUTPUT SETTINGS)
    # =======================================================
    def load_saved_directory(self):
        try:
            with open(self.local_config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                saved_dir = data.get("save_dir", "")
                if saved_dir and os.path.exists(saved_dir):
                    self.view.txt_save_dir.setText(saved_dir)
        except: 
            pass

    def browse_save_directory(self):
        current_dir = self.view.txt_save_dir.text() if self.view.txt_save_dir.text() else os.getcwd()
        folder = QFileDialog.getExistingDirectory(self.view, "Chọn thư mục lưu Video", current_dir)
        if folder:
            folder = os.path.normpath(folder)
            self.view.txt_save_dir.setText(folder)
            try:
                with open(self.local_config_file, 'w', encoding='utf-8') as f:
                    json.dump({"save_dir": folder}, f, indent=4)
            except: 
                pass

    # =======================================================
    # LOGIC: TRÍCH XUẤT VÀ HIỂN THỊ KẾT QUẢ CHATGPT
    # =======================================================
    def generate_prompts_with_chatgpt(self):
        current_paths = [dz.current_path for dz in self.view.drop_zones if dz.current_path]
        if not current_paths:
            QMessageBox.warning(self, "Thiếu ảnh", "Hãy chọn ít nhất 1 ảnh để làm kịch bản!")
            return
            
        scenario_data = self.view.cb_scenarios.currentData()
        if not scenario_data:
            QMessageBox.warning(self, "Thiếu kịch bản", "Vui lòng chọn một phong cách kịch bản!")
            return
            
        description = self.view.txt_description.toPlainText().strip()
        if not description:
            QMessageBox.warning(self, "Thiếu mô tả", "Hãy nhập mô tả sản phẩm!")
            return

        # Ráp Prompt tĩnh gửi lên ChatGPT
        system_prompt = scenario_data.get("system_prompt", "")
        final_prompt_to_send = f"{system_prompt}\n\nTHÔNG TIN SẢN PHẨM THỰC TẾ:\n{description}"
        
        # TRỘN LỜI THOẠI MẪU NẾU NGƯỜI DÙNG CUNG CẤP TRÊN UI
        viral_text = self.view.txt_viral_transcript.toPlainText().strip()
        if viral_text:
            final_prompt_to_send += f"\n\n[LỜI THOẠI VIRAL THAM KHẢO]:\n{viral_text}"

        self.view.clear_result_layout()
        self.view.btn_generate.setEnabled(False) 
        
        # Tạo nhãn trạng thái chờ
        self.status_label = QLabel("⏳ Đang gọi ChatGPT, vui lòng đợi (Tầm 15-30s)...")
        self.status_label.setStyleSheet("color: #ffb703; font-size: 14px; font-weight: bold; padding: 10px;")
        self.view.result_layout.addWidget(self.status_label)

        # Chạy luồng Worker (Sử dụng tệp ChatGPTWorker gốc của bạn)
        self.chat_worker = ChatGPTWorker(current_paths, final_prompt_to_send)
        self.chat_worker.finished.connect(self.on_chatgpt_finished)
        self.chat_worker.error.connect(self.on_chatgpt_error)
        self.chat_worker.start()

    def on_chatgpt_finished(self, result_data):
        self.view.btn_generate.setEnabled(True)
        self.view.clear_result_layout() # Xóa chữ Loading
        
        if not result_data or 'data' not in result_data:
            self.on_chatgpt_error("Dữ liệu ChatGPT trả về bị trống!")
            return
            
        chatgpt_json = result_data.get('data', {})
        variants = chatgpt_json.get('variants', [])
        
        if not variants:
            self.on_chatgpt_error("Dữ liệu trả về thiếu cấu trúc 'variants' hợp lệ.")
            return
            
        paths_used = result_data.get('paths', [])
        batch_id = f"Batch_Comp_{datetime.now().strftime('%H%M%S')}"

        # Rải danh sách ImageCard động lên Giao diện
        for i, item in enumerate(variants):
            card = ImageCard(paths_used) 
            gpt_prompt = item.get('veo_prompt', 'Lỗi phân tích cú pháp prompt.')
            hook_idea = item.get('hook_idea', f'Biến thể {i+1}')
            
            # Gán ID tác vụ để MainWindow định vị chuẩn card
            base_name = os.path.basename(paths_used[0]).split('.')[0] if paths_used else "Comp"
            card.task_id = f"{base_name}_comp_v{i}"
            
            card.prompt_display.setText(gpt_prompt)
            card.status_label.setText(f"🎯 {hook_idea}")
            card.status_label.setStyleSheet("color: #00BCD4; font-weight: bold;")
            
            # NỐI DÂY NÚT "TẠO VIDEO" LẺ TRÊN CARD
            card.btn_create_video.clicked.connect(
                lambda checked, c=card: self.mgr.main_window.add_to_video_queue(
                    image_path_list=c.img_paths, 
                    prompt=" ".join(c.prompt_display.toPlainText().split()), 
                    mode="components", 
                    batch_id=batch_id,
                    task_id_custom=c.task_id,
                    save_dir_override=self.view.txt_save_dir.text().strip()
                )
            )

            # Gán nút xóa Card
            card.btn_remove.clicked.connect(lambda _, c=card: self.remove_card(c))
            self.view.result_layout.addWidget(card)

    def on_chatgpt_error(self, error_message):
        self.view.btn_generate.setEnabled(True)
        self.view.clear_result_layout()
        lbl_err = QLabel(f"❌ Lỗi: {error_message}")
        lbl_err.setStyleSheet("color: red; font-size: 14px; font-weight: bold; padding: 10px;")
        self.view.result_layout.addWidget(lbl_err)
        QMessageBox.critical(self.view, "Lỗi ChatGPT", error_message)

    def remove_card(self, card_widget):
        self.view.result_layout.removeWidget(card_widget)
        card_widget.deleteLater()

    # =======================================================
    # LOGIC: ĐẨY TOÀN BỘ VÀO HÀNG ĐỢI RENDER (BATCH QUEUE)
    # =======================================================
    def push_to_render_queue(self):
        save_dir = self.view.txt_save_dir.text().strip()
        if not save_dir or not os.path.exists(save_dir):
            QMessageBox.warning(self.view, "Thiếu Thư Mục", "⚠️ Vui lòng chọn Thư Mục Lưu Video trước khi bấm Render!") # <-- Sửa self thành self.view
            return
            
        if self.view.result_layout.count() == 0:
            QMessageBox.warning(self.view, "Trống", "Chưa có kịch bản nào để Render!") # <-- Sửa self thành self.view
            return

        batch_id = f"Batch_Comp_{datetime.now().strftime('%H%M%S')}"
        cards_added = 0
        
        # Duyệt qua từng ImageCard có trên UI và đẩy vào hàng đợi
        for i in range(self.view.result_layout.count()):
            card = self.view.result_layout.itemAt(i).widget()
            if isinstance(card, ImageCard) and card.prompt_display.toPlainText().strip():
                
                # --- PHÒNG THỦ: Tự sinh task_id nếu trên UI bị thiếu để tránh lỗi ---
                if not hasattr(card, 'task_id') or not card.task_id:
                    base = os.path.basename(card.img_paths[0]).split('.')[0] if card.img_paths and card.img_paths[0] else "Comp"
                    card.task_id = f"{base}_comp_v{i}"

                raw_prompt = card.prompt_display.toPlainText()
                normalized_prompt = " ".join(raw_prompt.split())

                # Gửi yêu cầu nạp hàng đợi sang MainWindow
                self.mgr.main_window.add_to_video_queue(
                    image_path_list=card.img_paths, 
                    prompt=normalized_prompt, 
                    mode="components", 
                    batch_id=batch_id,
                    task_id_custom=card.task_id,
                    save_dir_override=save_dir 
                )
                cards_added += 1
                card.set_loading("Đang chờ Render...") 
                
        QMessageBox.information(self.view, "Thành công", f"Đã đẩy {cards_added} kịch bản vào Hàng đợi Render!") # <-- Sửa self thành self.view