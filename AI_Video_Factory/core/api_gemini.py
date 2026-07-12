import json
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted 
from PIL import Image
from core.key_manager import KeyManager
from core.logger import get_logger
import time

log = get_logger(__name__)

class GeminiAPI:
    def __init__(self, api_key: str = None):
        self.key_manager = KeyManager()
        self.model_name = 'gemini-1.5-flash'
        self._setup_client(api_key)

    def _setup_client(self, api_key):
        """Thiết lập hoặc đổi Key mới"""
        self.current_key = self.key_manager.get_current_key() or api_key
        if self.current_key:
            genai.configure(api_key=self.current_key)
            self.model = genai.GenerativeModel(self.model_name)

    def generate_with_image(self, image_path, instruction):
        """Hàm dùng chung: Gửi 1 ảnh + 1 lệnh -> Trả về JSON hoặc Text"""
        total_keys = len(self.key_manager.keys) or 1
        for attempt in range(total_keys):
            try:
                img = Image.open(image_path)
                response = self.model.generate_content([instruction, img])
                return response.text
            except ResourceExhausted:
                log.warning("Key Gemini #%d het quota, dang doi key khac...", attempt + 1)
                self.key_manager.rotate_key()
                self._setup_client(None)
                time.sleep(1)
            except Exception as e:
                log.error("Loi khi goi Gemini API (generate_with_image): %s", e, exc_info=True)
                break
        return None

    def translate_simple(self, text):
        """Dịch nhanh tên sản phẩm"""
        prompt = f"Translate to English, return only the word: {text}"
        try:
            res = self.model.generate_content(prompt)
            return res.text.strip()
        except Exception as e:
            # Fallback: neu dich loi thi tra ve nguyen van goc, khong chan luong chay,
            # nhung van log lai de biet ly do (VD: het quota, ten qua dai...).
            log.warning("Dich nhanh that bai cho '%s', giu nguyen text goc: %s", text, e)
            return text