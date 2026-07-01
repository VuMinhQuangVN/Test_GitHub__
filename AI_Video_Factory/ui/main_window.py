import sys, os, time
from datetime import datetime
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QTextEdit
from PyQt6.QtCore import pyqtSlot, Qt

# Import components & workers
from ui.components.sidebar import Sidebar
from ui.pages.banana_page import BananaPage
from ui.pages.frame_video_page import FrameVideoPage 
from ui.pages.text_video_page import TextVideoPage
from ui.components.image_card import ImageCard
from ui.pages.settings_page import SettingsPage
from ui.workers.image_worker import ImageWorker
from ui.workers.chat_worker import ChatGPTWorker
from ui.workers.video_worker import VideoWorker
from ui.pages.prompt_manager_page import PromptManagerPage
from ui.pages.video_merger_page import VideoMergerPage

class MainWindow(QMainWindow):
    def __init__(self, config_manager):
        super().__init__()
        self.mgr = config_manager
        self.mgr.main_window = self 
        
        from core.prompt_builder import PromptBuilder
        self.builder = PromptBuilder() 
        self.mgr.builder = self.builder 
        
        self.setWindowTitle("VEO3 ULTRA - AI VIDEO FACTORY")
        self.resize(1400, 950)
        self.chat_threads = [] 
        self.video_queue = []          
        self.active_video_workers = {} 

        with open("ui/assets/style.qss", "r", encoding="utf-8") as f:
            self.setStyleSheet(f.read())
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.nav_changed.connect(self.switch_page)
        main_layout.addWidget(self.sidebar)

        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)

        self.stack = QStackedWidget()
        self.page_text_vid = TextVideoPage(self.mgr)
        self.page_frame_vid = FrameVideoPage(self.mgr)
        self.page_banana = BananaPage(self.mgr)
        self.page_prompts = PromptManagerPage(self.mgr)
        self.page_merger = VideoMergerPage(self.mgr)
        self.page_settings = SettingsPage(self.mgr)

        self.page_frame_vid.start_all_production.connect(self.start_factory_queue)
        self.page_banana.request_generate.connect(self.handle_image_generation)

        self.stack.addWidget(self.page_text_vid)    
        self.stack.addWidget(self.page_frame_vid)   
        self.stack.addWidget(self.page_banana)      
        self.stack.addWidget(self.page_prompts)     
        self.stack.addWidget(QWidget())             
        self.stack.addWidget(self.page_merger)      
        self.stack.addWidget(self.page_settings)    
        
        self.sidebar.settings_btn.clicked.connect(lambda: self.switch_page("settings"))
        content_layout.addWidget(self.stack, 8)

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("background: #0b0d14; color: #4CAF50; font-family: Consolas; font-size: 11px;")
        content_layout.addWidget(self.log_display, 2)

        main_layout.addWidget(content_container, 4)
        self.switch_page("banana_pro")

    def log(self, message, status="INFO"): # Thêm status="INFO"
        ts = datetime.now().strftime("%H:%M:%S")
        # Hiển thị thêm status vào log cho chuyên nghiệp
        display_text = f"<b>[{ts}]</b> "
        if status != "INFO":
            display_text += f"<span style='color:red;'>[{status}]</span> "
        display_text += message
        
        self.log_display.append(display_text)
        print(f"[{ts}] [{status}] {message}")

    def switch_page(self, nav_id):
        mapping = {"txt_vid": 0, "frame_vid": 1, "banana_pro": 2, "prompt_mgr": 3, "merger": 5, "settings": 6}
        idx = mapping.get(nav_id, 2)
        self.stack.setCurrentIndex(idx)
        if nav_id == "settings": self.page_settings.refresh_acc_list()

    # ================================================================
    # GIAI ĐOẠN 1: TẠO ẢNH
    # ================================================================
    def handle_image_generation(self, data):
        self.page_banana.btn_run.setEnabled(False)
        self.mgr.save_sku_metadata(data["sku"], data["model_path"], data["prod_path"], data["bg_path"], data["type_vn"])
        
        self.current_sku_batch_id = f"Batch_{datetime.now().strftime('%H%M%S')}"
        
        # Khởi tạo Worker
        self.img_worker = ImageWorker(data, self.mgr)
        
        # --- KẾT NỐI TÍN HIỆU MỚI ---
        # Lắng nghe từng shot hoàn thành để xử lý Switch Account ngay tại đây
        self.img_worker.shot_completed.connect(self.on_parallel_shot_callback) 
        
        # Giữ lại các kết nối cũ nếu cần, hoặc dùng finished để mở khóa nút bấm
        self.img_worker.finished.connect(lambda: self.page_banana.btn_run.setEnabled(True))
        self.img_worker.start()
        self.log(f"🚀 Bắt đầu tiến trình tạo ảnh song song cho SKU: {data['sku']}")

    @pyqtSlot(dict)
    def on_parallel_shot_callback(self, result):
        shot_type = result['type']
        status = result['status']
        profile = result['profile']
        paths = result['paths']
        
        # --- TRƯỜNG HỢP 1: HẾT LƯỢT (SWITCH ACCOUNT) ---
        if status == "OUT_OF_CREDIT":
            self.log(f"🛑 Nick {profile} hết lượt tại shot {shot_type}. Đang đổi nick...")
            self.mgr.mark_chatgpt_empty(profile)
            
            # Tìm nick mới rảnh
            busy_nicks = [w.profile for w in self.img_worker.sub_workers if w.isRunning()]
            new_profile = self.mgr.get_safety_chatgpt_account(exclude_list=busy_nicks)
            
            if new_profile:
                self.log(f"🔄 Đã tìm thấy nick mới {new_profile}. Chạy lại shot {shot_type}...")
                # Lấy lại data gốc để biết đường dẫn ảnh tham chiếu
                data = result['data_origin']
                sku_dir = os.path.normpath(os.path.join(self.mgr.base_path, data['sku']))
                ref_imgs = [data["model_path"], data["prod_path"], data["bg_path"]]
                
                # Tìm lại task cụ thể cho shot này
                tasks = self.builder.get_image_tasks(data["scenario_key"], data["type_en"])
                current_task = next((t for t in tasks if t['type'] == shot_type), None)
                
                if current_task:
                    # Ra lệnh cho ImageWorker khởi động lại đúng shot đó với nick mới
                    self.img_worker.start_new_shot(new_profile, {**current_task, "sku": data['sku']}, sku_dir, ref_imgs)
                return
            else:
                self.log(f"❌ CẢNH BÁO: Không còn nick ChatGPT nào rảnh để đổi cho shot {shot_type}!", "FAIL")

        # --- TRƯỜNG HỢP 2: THÀNH CÔNG ---
        elif status == "SUCCESS":
            self.log(f"✨ Shot {shot_type} hoàn thành thành công.")
            # Chuyển sang giai đoạn tạo Card và hỏi kịch bản (Kế thừa logic cũ của bạn)
            self._process_single_success_shot(result)

        # --- TRƯỜNG HỢP 3: LỖI KHÁC ---
        else:
            self.log(f"⚠️ Shot {shot_type} gặp lỗi: {status}", "FAIL")

    def _process_single_success_shot(self, result):
        shot_type = result['type']
        paths = result['paths']
        scenario_key = self.page_banana.cb_shot_set.currentData()
        product_type = self.page_banana.cb_type.currentData()
        
        # Đọc cấu hình số lượng biến thể (variants) cần sinh cho shot này
        shot_cfg = self.builder.get_shot_config(scenario_key, shot_type)
        num_vars = shot_cfg.get("variants", 1)
        
        self.log(f"🌿 Shot {shot_type} yêu cầu dựng {num_vars} biến thể. Đang tiến hành hỏi gộp ChatGPT...")

        # 1. Vẽ (Spawn) toàn bộ Card lên giao diện UI trước
        spawned_cards = []
        for v_idx in range(num_vars):
            card = self._spawn_image_card(paths, shot_type, self.current_sku_batch_id, variant_index=v_idx)
            spawned_cards.append(card)
        
        # 2. Tạo câu lệnh mớm cho ChatGPT (Truyền num_variants chuẩn vào)
        instruction = self.builder.build_video_instruction(
            scenario_key, shot_type, product_type, num_variants=num_vars
        )
        
        # 3. Khởi tạo và kích hoạt 1 Worker duy nhất để lấy toàn bộ kịch bản
        chat_thread = ChatGPTWorker(paths, instruction)
        
        # Dùng Lambda truyền danh sách Card đã dựng vào hàm nhận kết quả (Thread-safe)
        chat_thread.finished.connect(
            lambda result_dict, cards=spawned_cards: self.on_batch_chat_finished(result_dict, cards)
        )
        
        chat_thread.start()
        self.chat_threads.append(chat_thread)
            
        # Chuyển trang để người dùng theo dõi các Card vừa hiện
        if self.stack.currentIndex() != 1: 
            self.switch_page("frame_vid")

    # === 2. HÀM NHẬN KẾT QUẢ GỘP TỪ CHATGPT VÀ PHÂN PHỐI ===
    def on_batch_chat_finished(self, result_dict, cards):
        if not result_dict or 'data' not in result_dict:
            self.log("❌ Lỗi: ChatGPT không trả về kết quả kịch bản hợp lệ.", "FAIL")
            for card in cards:
                card.status_label.setText("❌ Lỗi lấy kịch bản")
            return

        chat_json = result_dict.get('data', {})
        variants = chat_json.get('variants', [])
        
        # Cơ chế phòng thủ: Nếu ChatGPT lỡ trả về Object đơn thay vì List (Tương thích ngược)
        if not isinstance(variants, list):
            if 'prompt' in chat_json:
                variants = [chat_json]
            else:
                variants = []

        self.log(f"✅ Đã nhận xong kịch bản cho nhóm {len(cards)} Card.")
        
        # Phân phối lần lượt kịch bản vào từng Card tương ứng trên UI
        for i, card in enumerate(cards):
            if i < len(variants):
                variant_data = variants[i]
                # Chuẩn hóa lại cấu hình để tương thích 100% với hàm update_prompts có sẵn của Card
                card.update_prompts({"data": variant_data})
            else:
                card.status_label.setText("⚠️ Thiếu biến thể từ ChatGPT")


    # --- LUỒNG FLOW CŨ (Giữ nguyên cho bạn) ---
    @pyqtSlot(str, str, str)
    def on_image_downloaded(self, paths_str, base_prompt, shot_type):
        # Tách chuỗi ảnh thành list chuẩn
        img_paths_list = [p for p in paths_str.split("|") if p]
        
        scenario_key = self.page_banana.cb_shot_set.currentData()
        product_type = self.page_banana.cb_type.currentData()
        
        # Đọc cấu hình số lượng biến thể (variants) cho shot này
        shot_cfg = self.builder.get_shot_config(scenario_key, shot_type)
        num_vars = shot_cfg.get("variants", 1)

        self.log(f"🌿 [FLOW SEQUENTIAL] Shot {shot_type} vẽ xong. Đang dựng {num_vars} biến thể và gọi ChatGPT lấy kịch bản...")

        # 1. Vẽ (Spawn) toàn bộ Card lên giao diện UI trước
        spawned_cards = []
        for v_idx in range(num_vars):
            card = self._spawn_image_card(img_paths_list, shot_type, self.current_sku_batch_id, variant_index=v_idx)
            spawned_cards.append(card)

        # 2. Tạo câu lệnh mớm cho ChatGPT (Truyền num_variants chuẩn vào)
        instruction = self.builder.build_video_instruction(
            scenario_key, shot_type, product_type, num_variants=num_vars
        )

        # 3. Khởi tạo và kích hoạt 1 Worker duy nhất để lấy toàn bộ kịch bản
        chat_thread = ChatGPTWorker(img_paths_list, instruction)
        
        # Dùng Lambda truyền danh sách Card đã dựng vào hàm nhận kết quả gộp
        chat_thread.finished.connect(
            lambda result_dict, cards=spawned_cards: self.on_batch_chat_finished(result_dict, cards)
        )
        
        chat_thread.start()
        self.chat_threads.append(chat_thread)
        
        self.switch_page("frame_vid")

    def _spawn_image_card(self, img_paths, shot_type, batch_id, variant_index=0):
        card = ImageCard(img_paths)
        base_name = os.path.basename(img_paths[0]).split('.')[0]
        
        # Gán task_id duy nhất để không bị đè nhau trong Queue Video
        # Ví dụ: base_Ao_v0, base_Ao_v1, base_Ao_v2
        card.task_id = f"{base_name}_v{variant_index}"
        card.group_batch_id = batch_id 
        
        # Hiển thị số thứ tự biến thể trên UI cho dễ nhìn
        display_label = f"📸 {shot_type.upper()}"
        if variant_index > 0:
            display_label += f" (Var {variant_index + 1})"
        card.status_label.setText(display_label)
        
        card.btn_create_video.clicked.connect(
            lambda: self.add_to_video_queue(
                card.img_paths, 
                card.prompt_display.toPlainText(), 
                mode="frames", 
                batch_id=card.group_batch_id,
                task_id_custom=card.task_id
            )
        )
        self.page_frame_vid.add_production_card(card)
        return card
    # ================================================================
    # GIAI ĐOẠN 3: SẢN XUẤT VIDEO (QUEUE RENDER)
    # ================================================================
    # (Phần này giữ nguyên logic chuẩn của bạn)
    # def add_to_video_queue(self, image_path_list, prompt, mode="frames", batch_id=None, task_id_custom=None, variant_index=0):
    #     if task_id_custom: task_id = task_id_custom
    #     else:
    #         base = os.path.basename(image_path_list[0]).split('.')[0] if image_path_list else "TextVid"
    #         task_id = f"{base}_v{variant_index}"
        
    #     if any(t['id'] == task_id for t in self.video_queue) or task_id in self.active_video_workers: return

    #     self.video_queue.append({
    #         "id": task_id, "path": image_path_list, "prompt": prompt, 
    #         "mode": mode, "retry_count": 0, "batch_id": batch_id
    #     })
    #     self.process_video_queue()
    def add_to_video_queue(self, image_path_list, prompt, mode="frames", batch_id=None, task_id_custom=None, variant_index=0, save_dir_override=None):
        if task_id_custom: task_id = task_id_custom
        else:
            base = os.path.basename(image_path_list[0]).split('.')[0] if image_path_list else "TextVid"
            task_id = f"{base}_v{variant_index}"
        
        if any(t['id'] == task_id for t in self.video_queue) or task_id in self.active_video_workers: return

        self.video_queue.append({
            "id": task_id, "path": image_path_list, "prompt": prompt, 
            "mode": mode, "retry_count": 0, "batch_id": batch_id,
            "save_dir": save_dir_override # <--- NHẬN ĐƯỜNG DẪN TỪ UI COMPONENTS
        })
        self.process_video_queue()

    # def process_video_queue(self):
    #     while self.video_queue and len(self.active_video_workers) < 3:
    #         busy = [w.profile_name for w in self.active_video_workers.values()]
    #         profile = self.mgr.get_safety_account(exclude_list=busy)
    #         if not profile: break 

    #         task = self.video_queue.pop(0)
    #         self.update_factory_card_status(task['id'], f"Đang render ({profile})")
            
    #         # --- SỬA LỖI TẠI ĐÂY: Truyền task['batch_id'] vào Worker ---
    #         worker = VideoWorker(
    #             task['id'], 
    #             profile, 
    #             task['path'], 
    #             task['prompt'], 
    #             self.mgr, 
    #             batch_id=task['batch_id'], # <--- PHẢI CÓ DÒNG NÀY
    #             mode=task['mode']
    #         )
    #         # --------------------------------------------------------
            
    #         worker.finished_task.connect(self.on_video_finished)
    #         self.active_video_workers[task['id']] = worker
    #         worker.start()
    #         self.log(f"🚀 Render {task['id']} (Nick: {profile} | Nhóm: {task['batch_id']})")

    def process_video_queue(self):
        while self.video_queue and len(self.active_video_workers) < 3:
            busy = [w.profile_name for w in self.active_video_workers.values()]
            profile = self.mgr.get_safety_account(exclude_list=busy)
            if not profile: break 

            task = self.video_queue.pop(0)
            self.update_factory_card_status(task['id'], f"Đang render ({profile})")
            
            worker = VideoWorker(
                task['id'], 
                profile, 
                task['path'], 
                task['prompt'], 
                self.mgr, 
                batch_id=task['batch_id'], 
                mode=task['mode'],
                save_dir_override=task.get('save_dir') # <--- ĐẨY XUỐNG WORKER
            )
            
            worker.finished_task.connect(self.on_video_finished)
            self.active_video_workers[task['id']] = worker
            worker.start()
            self.log(f"🚀 Render {task['id']} (Nick: {profile} | Nhóm: {task['batch_id']})")

    @pyqtSlot(str, str, str)
    def on_video_finished(self, task_id, status, video_path):
        worker = self.active_video_workers.pop(task_id, None)
        if not worker: return
        if status == "SUCCESS":
            self.log(f"✅ XONG: {task_id}"); self.find_factory_card_and_set_success(task_id, video_path)
        elif status == "LOW_CREDITS":
            self.log(f"🛑 Hết lượt: {worker.profile_name}"); self.mgr.mark_account_empty(worker.profile_name)
            self.video_queue.insert(0, {"id": task_id, "path": worker.image_path, "prompt": worker.prompt, "mode": worker.mode, "retry_count": 0, "batch_id": worker.batch_id})
        else: self.update_factory_card_status(task_id, f"❌ Lỗi ({status})")
        self.process_video_queue()

    def update_factory_card_status(self, task_id, text):
        # Quét bên trang Frame (Cũ)
        grid1 = self.page_frame_vid.res_grid
        for i in range(grid1.count()):
            card = grid1.itemAt(i).widget()
            if hasattr(card, 'task_id') and card.task_id == task_id: card.set_loading(text); return
        
        # Quét bên trang Text/Components (Mới)
        grid2 = self.page_text_vid.result_layout
        for i in range(grid2.count()):
            card = grid2.itemAt(i).widget()
            if hasattr(card, 'task_id') and card.task_id == task_id: 
                card.set_loading(text)
                return

    def find_factory_card_and_set_success(self, task_id, video_path):
        # Quét bên trang Frame (Cũ)
        grid1 = self.page_frame_vid.res_grid
        for i in range(grid1.count()):
            card = grid1.itemAt(i).widget()
            if hasattr(card, 'task_id') and card.task_id == task_id: card.set_success(video_path); return
        
        # Quét bên trang Text/Components (Mới)
        grid2 = self.page_text_vid.result_layout
        for i in range(grid2.count()):
            card = grid2.itemAt(i).widget()
            if hasattr(card, 'task_id') and card.task_id == task_id: 
                card.set_success(video_path)
                return

    def start_factory_queue(self):
        batch_id = f"B_{datetime.now().strftime('%H%M%S')}"
        grid = self.page_frame_vid.res_grid
        for i in range(grid.count()):
            card = grid.itemAt(i).widget()
            if isinstance(card, ImageCard) and card.prompt_display.toPlainText().strip():
                self.add_to_video_queue(card.img_paths, " ".join(card.prompt_display.toPlainText().split()), mode="frames", batch_id=batch_id, task_id_custom=card.task_id)