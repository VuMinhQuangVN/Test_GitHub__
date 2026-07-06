from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

class BasePage:
    def __init__(self, page: Page):
        self.page = page

    def goto(self, url: str):
        """Điều hướng trang với cơ chế đợi nạp DOM"""
        try:
            print(f"🌐 [NAVIGATE] Truy cập: {url}")
            self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"❌ [NAVIGATE] Lỗi truy cập {url}: {e}")

    def wait_for_element(self, locator: str, timeout: int = 30000, state: str = "visible"):
        """Đợi một phần tử đạt trạng thái mong muốn (visible, hidden, attached)"""
        try:
            self.page.locator(locator).wait_for(state=state, timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            return False

    def force_click(self, locator: str):
        """Click cưỡng ép xuyên qua các lớp phủ mờ"""
        if self.wait_for_element(locator):
            self.page.locator(locator).first.click(force=True)
            return True
        return False

    def input_text(self, locator: str, text: str):
        """Xóa trắng và điền văn bản vào khung nhập liệu"""
        if self.wait_for_element(locator):
            loc = self.page.locator(locator).first
            loc.fill("") # Xóa sạch trước khi điền
            loc.fill(text)
            return True
        return False

    def is_visible(self, locator: str, timeout: int = 5000) -> bool:
        """Kiểm tra nhanh xem phần tử có đang hiện trên màn hình không"""
        try:
            return self.page.locator(locator).first.is_visible(timeout=timeout)
        except:
            return False