from PyQt6.QtCore import QThread, pyqtSignal
from playwright.sync_api import sync_playwright
from core.browser_manager import BrowserManager
from core.logger import get_logger

log = get_logger(__name__)


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
                
                log.info("Dang mo trinh duyet cho %s. Vui long dang nhap thu cong...", self.profile_name)
                
                # Giữ trình duyệt mở cho đến khi người dùng tự tay đóng cửa sổ Chrome
                while True:
                    if context.pages == [] or page.is_closed():
                        break
                    self.msleep(500)
                
                context.close()
        except Exception as e:
            log.error("Loi khi mo trinh duyet dang nhap (%s): %s", self.profile_name, e, exc_info=True)
        self.finished.emit()