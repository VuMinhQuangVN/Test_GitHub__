import json
import os
from core.logger import get_logger

log = get_logger(__name__)


class KeyManager:
    def __init__(self, db_path="database/api_keys.json"):
        self.db_path = db_path
        self.keys = []
        self.current_index = 0
        self.load_keys()

    def load_keys(self):
        """Đọc danh sách Key từ file JSON một cách an toàn"""
        if not os.path.exists(self.db_path) or os.path.getsize(self.db_path) == 0:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump({"gemini_keys": [], "current_index": 0}, f, indent=4)
            return

        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.keys = data.get("gemini_keys", [])
                self.current_index = data.get("current_index", 0)
        except json.JSONDecodeError as e:
            log.warning("File %s bi hong/khong doc duoc JSON, dung danh sach key rong: %s", self.db_path, e)
            self.keys = []

    def get_current_key(self):
        if not self.keys: return None
        if self.current_index >= len(self.keys): self.current_index = 0
        return self.keys[self.current_index]

    def rotate_key(self):
        """Xoay vòng sang Key tiếp theo và lưu lại trạng thái"""
        if not self.keys: return None
        
        self.current_index = (self.current_index + 1) % len(self.keys)
        
        # Lưu index mới vào JSON để lần sau mở app vẫn nhớ
        data = {"gemini_keys": self.keys, "current_index": self.current_index}
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            
        log.info("Da doi sang API Key vi tri: %d", self.current_index + 1)
        return self.keys[self.current_index]