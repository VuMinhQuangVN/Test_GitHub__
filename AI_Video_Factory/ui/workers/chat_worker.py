import os
import time
import uuid
from PyQt6.QtCore import QThread, pyqtSignal
from playwright.sync_api import sync_playwright
from core.browser_manager import BrowserManager
from bots.chatgpt_page import ChatGPTPage

class ChatGPTWorker(QThread):
    # Trả về dict chứa: 'paths' (list ảnh) và 'data' (JSON kịch bản)
    finished = pyqtSignal(dict) 
    error = pyqtSignal(str) # Thêm tín hiệu báo lỗi về UI

    def __init__(self, image_paths: list, prompt_request: str):
        super().__init__()
        self.image_paths = [p for p in image_paths if p and os.path.exists(p)]
        self.prompt_request = prompt_request
        # TẠO TÊN PROFILE RIÊNG BIỆT: Tránh việc nhiều luồng tranh nhau 1 folder
        # Chúng ta thêm một ID ngắn vào sau để mỗi lần chạy là 1 folder khác nhau
        self.unique_id = str(uuid.uuid4())[:8]
        self.profile_name = f"chatgpt_guest_{self.unique_id}"

    def run(self):
        print(f"🤖 [CHAT-WORKER] Khởi tạo luồng khách mới: {self.profile_name}")
        
        mgr = BrowserManager(profile_name=self.profile_name)
        
        # BƯỚC 1: Đảm bảo sạch sẽ trước khi chạy
        mgr.hard_reset_profile() 
        
        try:
            with sync_playwright() as p:
                # 2. Khởi tạo trình duyệt
                # Thêm khoảng nghỉ nhỏ để Windows kịp cấp quyền tạo folder
                time.sleep(1)
                context = mgr.init_browser(p)
                page = context.pages[0]
                
                chat_bot = ChatGPTPage(page)
                
                # 3. Truy cập ChatGPT
                chat_bot.navigate()
                
                # 4. Upload ảnh và lấy Prompt
                # Lưu ý: Hàm này trong chatgpt_page.py phải xử lý click X popup
                result = chat_bot.get_scripts_with_images(self.image_paths, self.prompt_request)
                
                if result:
                    print(f"✅ [CHAT-WORKER] Đã lấy xong kịch bản cho: {os.path.basename(self.image_paths[0])}")
                    self.finished.emit({
                        "paths": self.image_paths, 
                        "data": result
                    })
                else:
                    print(f"⚠️ [CHAT-WORKER] ChatGPT trả về rỗng.")
                    self.error.emit("ChatGPT không trả về kịch bản hợp lệ.")

                # 5. Đóng trình duyệt
                context.close()
                
                # 6. Dọn dẹp & Xóa sổ folder tạm (Tẩy não + Hút mỡ)
                mgr.cleanup_profile()
                mgr.hard_reset_profile()
                
                # 7. Xóa folder rỗng sau khi reset thành công (Tùy chọn)
                try:
                    full_path = mgr.profile_dir
                    if os.path.exists(full_path):
                        import shutil
                        shutil.rmtree(full_path)
                except: pass

        except Exception as e:
            error_msg = f"Lỗi luồng ChatGPT ({self.profile_name}): {str(e)}"
            print(f"❌ {error_msg}")
            self.error.emit(error_msg)