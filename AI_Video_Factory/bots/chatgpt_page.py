import time
import json
import re
import os
from bots.base_page import BasePage

class ChatGPTPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.url = "https://chatgpt.com/"
        self.locators = {
            "file_input": "input[type='file']",
            "prompt_box": "#prompt-textarea",
            "btn_stop": "[aria-label='Stop generating']",
            "btn_idle_state": "[data-testid='composer-speech-button']",
            "markdown_response": "div.markdown.prose",
            # Nút X (Dựa trên data-testid bạn chụp)
            "btn_close_dialog": "button[data-testid='close-button']",
            # Selector cho cả cái Dialog to
            "dialog_overlay": "div[role='dialog']"
        }

    def navigate(self):
        self.goto(self.url)
        time.sleep(4)
        self.handle_popups()
        try:
            self.page.locator(self.locators["prompt_box"]).click(timeout=5000)
        except:
            # Click vào vùng an toàn để lấy focus
            self.page.mouse.click(100, 100)

    def handle_popups(self):
        """Hàm xử lý Popup Đăng nhập: Thử bấm X, nếu không được thì bấm vùng trống"""
        try:
            # 1. Thử tìm nút X chính xác
            close_btn = self.page.locator(self.locators["btn_close_dialog"]).first
            if close_btn.is_visible(timeout=1500):
                print("⚠️ [CHATGPT] Bấm nút X để tắt bảng Đăng nhập.")
                close_btn.click(force=True)
                time.sleep(1)
                return

            # 2. Nếu không thấy X nhưng thấy Dialog đang mở, click vào 'Vùng chết'
            if self.page.locator(self.locators["dialog_overlay"]).first.is_visible(timeout=500):
                print("⚠️ [CHATGPT] Click vùng trống để thoát Overlay.")
                # Click vào góc trên bên trái (thường là vùng an toàn thoát modal)
                self.page.mouse.click(10, 10)
                time.sleep(1)
        except:
            pass

    def get_scripts_with_images(self, image_paths: list, prompt_text: str):
        try:
            # Luôn dọn đường trước khi làm
            self.handle_popups()

            # 1. Nạp ảnh
            print(f"📤 [CHATGPT] Đang tải {len(image_paths)} ảnh tham chiếu...")
            self.page.locator(self.locators["file_input"]).last.set_input_files(image_paths)
            
            # Đợi thumbnail hiện
            time.sleep(12)

            # 2. Nhập Prompt
            print("✍️ [CHATGPT] Đang điền yêu cầu kịch bản...")
            self.handle_popups() # Check popup lần nữa trước khi fill
            
            box = self.page.locator(self.locators["prompt_box"])
            box.click(force=True)
            box.fill(prompt_text)
            time.sleep(30)

            print("✍️ [CHATGPT] Enter...")
            # 3. Gửi lệnh
            self.page.keyboard.press("Enter")
            
            # 4. Đợi AI (Kiểm tra popup trong lúc chờ)
            if self._wait_for_ai_completion():
                return self._extract_json_from_chat()
            
            return None

        except Exception as e:
            print(f"❌ [CHATGPT-PAGE] Lỗi: {e}")
            return None

    def _wait_for_ai_completion(self, timeout_seconds=180):
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            # ChatGPT hay hiện popup 'Đăng nhập' ngay khi AI đang viết được nửa chừng
            self.handle_popups()
            
            is_writing = self.is_visible(self.locators["btn_stop"], timeout=1000)
            is_idle = self.is_visible(self.locators["btn_idle_state"], timeout=1000)
            if not is_writing and is_idle:
                time.sleep(2)
                return True
            time.sleep(3)
        return False

    def _extract_json_from_chat(self):
        try:
            content = self.page.locator(self.locators["markdown_response"]).last.inner_text()
            match = re.search(r'(\[.*\]|\{.*\})', content, re.DOTALL)
            return json.loads(match.group(1)) if match else None
        except:
            return None
