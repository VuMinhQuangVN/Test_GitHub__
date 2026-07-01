from PyQt6.QtCore import QThread, pyqtSignal
from playwright.sync_api import sync_playwright
from core.browser_manager import BrowserManager

class LoginWorker(QThread):
    finished = pyqtSignal()

    def __init__(self, profile_name):
        super().__init__()
        self.profile_name = profile_name

    def run(self):
        try:
            with sync_playwright() as p:
                bm = BrowserManager(profile_name=self.profile_name)
                # Mở trình duyệt có giao diện (headless=False)
                context = bm.init_browser(p)
                page = context.pages[0]
                
                # Truy cập thẳng vào trang login hoặc Google Flow
                page.goto("https://labs.google/fx/vi/tools/flow")
                
                print(f"🔑 Đang mở trình duyệt cho {self.profile_name}. Vui lòng đăng nhập thủ công...")
                
                # Giữ trình duyệt mở cho đến khi người dùng tự tay đóng cửa sổ Chrome
                while True:
                    if context.pages == [] or page.is_closed():
                        break
                    self.msleep(500)
                
                context.close()
        except Exception as e:
            print(f"❌ Lỗi khi mở trình duyệt đăng nhập: {e}")
        self.finished.emit()