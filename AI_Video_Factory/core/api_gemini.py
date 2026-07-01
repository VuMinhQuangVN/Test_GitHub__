import json
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted 
from PIL import Image
from core.key_manager import KeyManager
import time

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
                print(f"⚠️ Key {attempt+1} hết hạn. Đang đổi...")
                self.key_manager.rotate_key()
                self._setup_client(None)
                time.sleep(1)
            except Exception as e:
                print(f"❌ Lỗi API: {e}")
                break
        return None

    def translate_simple(self, text):
        """Dịch nhanh tên sản phẩm"""
        prompt = f"Translate to English, return only the word: {text}"
        try:
            res = self.model.generate_content(prompt)
            return res.text.strip()
        except: return text