import os, time, re, random
from PyQt6.QtCore import QThread, pyqtSignal
from playwright.sync_api import sync_playwright
from core.browser_manager import BrowserManager
from core.prompt_builder import PromptBuilder
from pages.flow_image import FlowImagePage
from pages.chatgpt_images_page import ChatGPTImagesPage

# ================================================================
# WORKER CON: VẼ ẢNH CHO 1 SHOT (CHUYÊN TRÁCH CHATGPT)
# ================================================================
class SingleShotChatGPTWorker(QThread):
    # Trả về: shot_type, paths, status, profile_name
    shot_finished = pyqtSignal(str, list, str, str)

    def __init__(self, profile, task, sku_dir, data_refs, mgr):
        super().__init__()
        self.profile = profile
        self.task = task
        self.sku_dir = sku_dir
        self.refs = data_refs
        self.mgr = mgr
    
    def run(self):
        try:
            with sync_playwright() as p:
                bm = BrowserManager(profile_name=self.profile)
                context = bm.init_browser(p, headless=False)
                page = context.pages[0]
                bot = ChatGPTImagesPage(page)
                bot.navigate()

                upload_status = bot.upload_references(self.refs)

                # 1. Xử lý lỗi Limit ngay khi Upload
                if upload_status == "LIMIT_REACHED":
                    self.shot_finished.emit(self.task['type'], [], "OUT_OF_CREDIT", self.profile)
                    context.close(); return

                if upload_status is True:
                    prefix = f"base_{self.task['sku']}_{self.task['type']}"
                    
                    # --- TẠO ẢNH A ---
                    res_a = bot.generate_step(self.task['prompt'], 
                                            os.path.normpath(os.path.join(self.sku_dir, f"{prefix}_A.jpg")), 
                                            f"{self.task['type']} Start")
                    
                    if res_a == "OUT_OF_CREDIT":
                        self.shot_finished.emit(self.task['type'], [], "OUT_OF_CREDIT", self.profile)
                        context.close(); return

                    results = [res_a] if res_a else []

                    # --- TẠO ẢNH B ---
                    target_count = self.task.get('target_count', 1)
                    pose_req = self.task.get('pose_change_request')

                    if target_count == 2 and res_a and pose_req:
                        res_b = bot.generate_step(pose_req, 
                                                os.path.normpath(os.path.join(self.sku_dir, f"{prefix}_B.jpg")), 
                                                f"{self.task['type']} End")
                        
                        if res_b == "OUT_OF_CREDIT":
                            if res_a and os.path.exists(res_a):
                                try: os.remove(res_a)
                                except: pass
                            self.shot_finished.emit(self.task['type'], [], "OUT_OF_CREDIT", self.profile)
                            context.close(); return
                        
                        if res_b: results.append(res_b)

                    context.close()
                    status = "SUCCESS" if len(results) == target_count else "ERROR"
                    self.shot_finished.emit(self.task['type'], results, status, self.profile)
                else:
                    self.shot_finished.emit(self.task['type'], [], "UPLOAD_FAIL", self.profile)
                    context.close()
        except Exception as e:
            print(f"❌ [SHOT-WORKER] Crash: {e}")
            self.shot_finished.emit(self.task['type'], [], "ERROR", self.profile)

# ================================================================
# WORKER MẸ: QUẢN LÝ TÁC VỤ (DISPATCHER)
# ================================================================
class ImageWorker(QThread):
    # Tín hiệu báo cáo từng shot về MainWindow
    shot_completed = pyqtSignal(dict) 
    finished = pyqtSignal()

    def __init__(self, data, config_mgr):
        super().__init__()
        self.data = data
        self.mgr = config_mgr
        self.builder = PromptBuilder()
        self.sub_workers = []

    def run(self):
        engine = self.data.get("engine", "flow_sequential")
        if engine == "chatgpt_parallel":
            self.run_chatgpt_parallel()
        else:
            self.run_flow_sequential()

    def run_chatgpt_parallel(self):
        sku = self.data["sku"]
        sku_dir = os.path.normpath(os.path.join(self.mgr.base_path, sku))
        tasks = self.builder.get_image_tasks(self.data["scenario_key"], self.data["type_en"])
        ref_imgs = [self.data["model_path"], self.data["prod_path"], self.data["bg_path"]]

        for task in tasks:
            # MainWindow sẽ quản lý việc chọn nick, ở đây ta chỉ lấy nick rảnh
            profile = self.mgr.get_safety_chatgpt_account(exclude_list=[w.profile for w in self.sub_workers if w.isRunning()])
            if not profile: 
                # Nếu hết nick ngay từ đầu, báo lỗi cho MainWindow xử lý
                self.shot_completed.emit({"type": task['type'], "status": "NO_ACCOUNT"})
                continue
            
            task_with_sku = {**task, "sku": sku} 
            self.start_new_shot(profile, task_with_sku, sku_dir, ref_imgs)
            time.sleep(15) # Giãn cách mở browser

    def run_flow_sequential(self):
        """LUỒNG TUẦN TỰ: 1 trình duyệt, làm lần lượt từng Shot (Engine Flow cũ)"""
        sku = self.data["sku"]
        sku_dir = os.path.normpath(os.path.join(self.mgr.base_path, sku))
        os.makedirs(sku_dir, exist_ok=True)
        tasks = self.builder.get_image_tasks(self.data["scenario_key"], self.data["type_en"])
        
        profile_name = "chrome_auto_profile"

        try:
            with sync_playwright() as p:
                bm = BrowserManager(profile_name=profile_name)
                context = bm.init_browser(p)
                page = context.pages[0]
                bot = FlowImagePage(page)
                bot.navigate()

                # --- BƯỚC CHUẨN BỊ (Click Dự án mới) ---
                bot.page.locator(bot.locators["btn_new_project"]).first.click()
                time.sleep(2)
                
                # --- THAY THẾ TOÀN BỘ LOGIC UPLOAD CŨ BẰNG BATCH UPLOAD SIÊU TỐC ---
                ref_images = [self.data["model_path"], self.data["prod_path"], self.data["bg_path"]]
                upload_status = bot.upload_references_batch(ref_images)
                
                if not upload_status:
                    self.shot_completed.emit({"type": "ALL", "status": "UPLOAD_FAIL", "profile": profile_name})
                    context.close()
                    return

                bot._configure_settings()

                # --- VÒNG LẶP CHẠY TỪNG SHOT (GIỮ NGUYÊN) ---
                for task in tasks:
                    shot_type = task['type']
                    bot.page.keyboard.press("Escape")
                    editor = bot.page.locator(bot.locators["input_prompt"]).first
                    editor.click()
                    bot.page.keyboard.press("Control+A")
                    bot.page.keyboard.press("Backspace")

                    all_ok = True
                    for img_p in ref_images:
                        if img_p and not bot._select_reference_from_library(os.path.basename(img_p)):
                            all_ok = False; break
                    if not all_ok: 
                        self.shot_completed.emit({"type": shot_type, "status": "REF_NOT_FOUND", "profile": profile_name})
                        continue

                    initial_total = bot.get_current_thumb_count()
                    editor.click()
                    bot.page.keyboard.insert_text(task["prompt"])
                    bot.page.locator(bot.locators["btn_generate"]).first.click()

                    new_count = bot.monitor_render(initial_total, batch_limit=task['target_count'])
                    if new_count > 0:
                        paths = bot.download_batch(new_count, sku_dir, sku, shot_type)
                        self.shot_completed.emit({
                            "type": shot_type,
                            "paths": paths,
                            "status": "SUCCESS",
                            "profile": profile_name,
                            "data_origin": self.data
                        })
                    else:
                        self.shot_completed.emit({
                            "type": shot_type,
                            "paths": [],
                            "status": "RENDER_FAIL",
                            "profile": profile_name,
                            "data_origin": self.data
                        })
                
                context.close()
                bm.cleanup_profile()
        except Exception as e:
            print(f"❌ [FLOW-SEQUENTIAL] Lỗi: {e}")
            
        self.finished.emit()

    def start_new_shot(self, profile, task, sku_dir, ref_imgs):
        """Hàm này có thể được gọi từ MainWindow để Retry"""
        worker = SingleShotChatGPTWorker(profile, task, sku_dir, ref_imgs, self.mgr)
        worker.shot_finished.connect(self._on_sub_worker_done)
        self.sub_workers.append(worker)
        worker.start()

    def _on_sub_worker_done(self, shot_type, paths, status, profile):
        # Đóng gói dữ liệu gửi thẳng về MainWindow
        result = {
            "type": shot_type,
            "paths": paths,
            "status": status,
            "profile": profile,
            "data_origin": self.data # Gửi kèm data gốc để MainWindow biết đường retry
        }
        self.shot_completed.emit(result)
        
        # Kiểm tra xem còn luồng nào đang chạy không
        if not any(w.isRunning() for w in self.sub_workers):
            self.finished.emit()