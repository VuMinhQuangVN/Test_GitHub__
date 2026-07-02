import os, time, random, re
from PyQt6.QtCore import QThread, pyqtSignal
from playwright.sync_api import sync_playwright
from core.browser_manager import BrowserManager

# Import cả 2 trang lõi
from pages.flow_page import FlowPage
from pages.flow_components_page import FlowComponentsPage # <--- BOT MỚI

class VideoWorker(QThread):
    finished_task = pyqtSignal(str, str, str)

    def __init__(self, task_id, profile_name, image_path, prompt, mgr, retry_count=0, batch_id=None, mode="frames", save_dir_override=None):
        super().__init__()
        self.task_id = task_id
        self.profile_name = profile_name
        self.image_path = image_path
        self.prompt = prompt
        self.mgr = mgr
        self.retry_count = retry_count
        self.batch_id = batch_id
        self.mode = mode
        self.save_dir_override = save_dir_override # <--- Tham số mới nhận từ MainWindow

    def run(self):
        # GIÃN CÁCH 2 GIÂY/NICK
        try: acc_num = int(re.search(r'\d+', self.profile_name).group())
        except: acc_num = 0
        wait_time = (acc_num * 2) + random.uniform(0.5, 1.5)
        print(f"⏳ [WORKER] {self.profile_name} chờ {wait_time:.1f}s trước khi chạy...")
        time.sleep(wait_time)
        
        os.makedirs("logs", exist_ok=True)
        trace_path = f"logs/trace_{self.task_id}.zip"
        
        try:
            with sync_playwright() as p:
                bm = BrowserManager(profile_name=self.profile_name)
                context = bm.init_browser(p, headless=False)
                context.tracing.start(screenshots=True, snapshots=True, sources=True)
                page = context.pages[0]

                # XÁC ĐỊNH THƯ MỤC LƯU FILE
                valid_paths = [p for p in self.image_path if p and os.path.exists(str(p))]
                
                if self.save_dir_override and os.path.exists(self.save_dir_override):
                    # Nếu có truyền đường dẫn riêng (từ trang Components)
                    sku_folder = self.save_dir_override
                else:
                    # Logic cũ (lấy theo thư mục ảnh)
                    if valid_paths: 
                        img_dir = os.path.dirname(valid_paths[0])
                        
                        # Nếu ảnh nằm trong thư mục "base_image" hoặc "images", lùi 1 cấp để ra thư mục SKU gốc
                        if os.path.basename(img_dir) in ["base_image", "images", "base_images"]:
                            sku_folder = os.path.dirname(img_dir)
                        else:
                            sku_folder = img_dir
                    else: sku_folder = os.path.join(self.mgr.base_path, "Text_To_Video_Factory")

                current_run_id = self.batch_id if self.batch_id else f"Run_{time.strftime('%H%M%S')}"

                # ========================================================
                # 🚀 LOGIC RẼ NHÁNH: CHỌN ĐÚNG BOT ĐỂ CHẠY
                # ========================================================
                if self.mode == "components":
                    # --- CHẠY CHẾ ĐỘ THÀNH PHẦN (NHIỀU ẢNH + AUTO FILL @) ---
                    bot = FlowComponentsPage(page)
                    bot.navigate()
                    res_status = bot.create_video_components(
                        image_paths=valid_paths, 
                        prompt_text=self.prompt,
                        save_dir=sku_folder, 
                        profile_name=self.profile_name,
                        sku=self.task_id, 
                        model_type="Lite", 
                        batch_id=current_run_id
                    )
                else:
                    # --- CHẠY CHẾ ĐỘ KHUNG HÌNH (CŨ - 2 ẢNH) ---
                    bot = FlowPage(page)
                    bot.navigate()
                    res_status = bot.create_video(
                        image_path=valid_paths, 
                        prompt_text=self.prompt,
                        save_dir=sku_folder, 
                        profile_name=self.profile_name,
                        sku=self.task_id, 
                        mode=self.mode, 
                        model_type="Lite", 
                        batch_id=current_run_id
                    )
                # ========================================================

                context.tracing.stop(path=None if res_status and os.path.exists(str(res_status)) else trace_path)
                context.close()
                bm.cleanup_profile()

                # XỬ LÝ KẾT QUẢ TRẢ VỀ
                if res_status == "OUT_OF_CREDIT":
                    self.finished_task.emit(self.task_id, "LOW_CREDITS", "")
                elif res_status and os.path.exists(str(res_status)):
                    self.finished_task.emit(self.task_id, "SUCCESS", str(res_status))
                else:
                    self.finished_task.emit(self.task_id, str(res_status), "")

        except Exception as e:
            print(f"❌ [WORKER] Crash hệ thống {self.profile_name}: {e}")
            try: context.tracing.stop(path=trace_path)
            except: pass
            self.finished_task.emit(self.task_id, "SYSTEM_CRASH", "")