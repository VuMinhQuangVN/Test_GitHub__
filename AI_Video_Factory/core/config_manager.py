# import json
# import os
# from datetime import datetime

# class ConfigManager:
#     def __init__(self, base_storage_path="F:/Data_Tool"):
#         self.base_path = os.path.normpath(base_storage_path)
#         self.db_dir = "database"
#         self.profiles_dir = os.path.join(os.getcwd(), "profiles")
        
#         self.paths = {
#             "products": os.path.join(self.db_dir, "products.json"),
#             "settings": os.path.join(self.db_dir, "settings.json"),
#             "prompts": os.path.join(self.db_dir, "prompts_db.json"),
#             "account": os.path.join(self.db_dir, "account_status.json")
#         }

#         os.makedirs(self.db_dir, exist_ok=True)
#         os.makedirs(self.profiles_dir, exist_ok=True)
#         if not os.path.exists(self.base_path):
#             os.makedirs(self.base_path, exist_ok=True)

#     def load_json(self, file_key, default_data=None):
#         path = self.paths.get(file_key, file_key)
#         if os.path.exists(path) and os.path.getsize(path) > 0:
#             try:
#                 with open(path, "r", encoding="utf-8") as f:
#                     return json.load(f)
#             except: pass
#         return default_data if default_data is not None else {}

#     def save_json(self, file_key, data):
#         path = self.paths.get(file_key, file_key)
#         with open(path, "w", encoding="utf-8") as f:
#             json.dump(data, f, indent=4, ensure_ascii=False)

#     def get_sku_metadata(self, sku):
#         info_path = os.path.join(self.base_path, sku, "info.json")
#         return self.load_json(info_path, None)

#     def save_sku_metadata(self, sku, model_path, prod_path, bg_path, product_type_vn):
#         sku_dir = os.path.join(self.base_path, sku)
#         os.makedirs(sku_dir, exist_ok=True)
#         metadata = {
#             "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#             "fixed_model_path": model_path,
#             "product_img_path": prod_path,
#             "background_path": bg_path,
#             "product_type_vn": product_type_vn
#         }
#         self.save_json(os.path.join(sku_dir, "info.json"), metadata)

#     def get_existing_skus(self):
#         try:
#             if not os.path.exists(self.base_path): return []
#             return sorted([d for d in os.listdir(self.base_path) 
#                           if os.path.isdir(os.path.join(self.base_path, d))])
#         except: return []

#     def get_all_profiles(self):
#         try:
#             profiles = [d for d in os.listdir(self.profiles_dir) 
#                         if os.path.isdir(os.path.join(self.profiles_dir, d))]
#             if "chrome_auto_profile" in profiles:
#                 profiles.remove("chrome_auto_profile")
#                 profiles.insert(0, "chrome_auto_profile")
#             return profiles
#         except: return []

#     def get_safety_account(self, exclude_list=None):
#         """Lấy Nick rảnh, tuyệt đối không trùng với các luồng đang chạy"""
#         exclude_list = exclude_list or []
#         account_db = self.load_json("account")
#         today = datetime.now().strftime("%Y-%m-%d")
        
#         # Thử 7 nick Free trước
#         free_profiles = [f"google_acc_{i}" for i in range(1, 8)]
#         for profile in free_profiles:
#             if profile in exclude_list: continue
            
#             acc_info = account_db.get(profile, {})
#             is_empty = (acc_info.get("status") == "empty" and acc_info.get("date") == today)
#             if not is_empty:
#                 return profile

#         # Kiểm tra Nick PRO cuối cùng
#         pro_profile = "chrome_auto_profile"
#         if pro_profile not in exclude_list:
#             acc_info = account_db.get(pro_profile, {})
#             is_empty = (acc_info.get("status") == "empty" and acc_info.get("date") == today)
#             if not is_empty:
#                 return pro_profile
        
#         print("⚠️ [CONFIG] CẢNH BÁO: Không còn nick nào rảnh hoặc còn token cho ngày hôm nay!")
#         return None

#     def get_safety_chatgpt_account(self, exclude_list=None):
#         exclude_list = exclude_list or []
#         # Dùng file json riêng để không lẫn lộn với lượt Video
#         account_db = self.load_json("chatgpt_account_status")
#         today = datetime.now().strftime("%Y-%m-%d")
        
#         # Thử 7 nick
#         for i in range(1, 8):
#             profile = f"google_acc_{i}"
#             if profile in exclude_list: continue
            
#             acc_info = account_db.get(profile, {})
#             is_empty = (acc_info.get("status") == "empty" and acc_info.get("date") == today)
#             if not is_empty:
#                 return profile
#         return None

#     def mark_chatgpt_empty(self, profile_name):
#         accounts = self.load_json("chatgpt_account_status")
#         accounts[profile_name] = {"status": "empty", "date": datetime.now().strftime("%Y-%m-%d")}
#         self.save_json("chatgpt_account_status", accounts)
        
#     def mark_account_empty(self, profile_name):
#         accounts = self.load_json("account")
#         accounts[profile_name] = {"status": "empty", "date": datetime.now().strftime("%Y-%m-%d")}
#         self.save_json("account", accounts)

#     def get_upload_display_name(self, source):
#         """
#         Lấy displayName từ cấu trúc JSON upload.
#         'source' có thể là đường dẫn file (str) hoặc dữ liệu dict trực tiếp.
#         """
#         # 1. Nếu source là đường dẫn file, nạp nó lên
#         if isinstance(source, str):
#             data = self.load_json(source)
#         else:
#             data = source

#         # 2. Bốc giá trị displayName theo cấu trúc lồng nhau
#         # workflow -> metadata -> displayName
#         try:
#             display_name = data.get("workflow", {}).get("metadata", {}).get("displayName")
#             return display_name # Trả về string hoặc None nếu không thấy
#         except Exception:
#             return None
import json
import os
from datetime import datetime

class ConfigManager:
    def __init__(self, base_storage_path="F:/Data_Tool"):
        # Đường dẫn gốc cho luồng Frame cũ
        self.base_path = os.path.normpath(base_storage_path)
        
        # Tổ chức lại thư mục Database cho gọn gàng khi scale dự án
        self.db_dir = "database"
        self.prompts_dir = os.path.join(self.db_dir, "prompts")
        self.settings_dir = os.path.join(self.db_dir, "settings")
        self.profiles_dir = os.path.join(os.getcwd(), "profiles")
        
        self.paths = {
            # --- DATA CỦA LUỒNG FRAME (CŨ) ---
            "products": os.path.join(self.db_dir, "products.json"),
            "settings": os.path.join(self.db_dir, "settings.json"),
            "prompts": os.path.join(self.db_dir, "prompts_db.json"),
            "account": os.path.join(self.db_dir, "account_status.json"),
            "chatgpt_account_status": os.path.join(self.db_dir, "chatgpt_account_status.json"),
            
            # --- DATA CỦA LUỒNG THÀNH PHẦN (MỚI BỔ SUNG) ---
            "comp_scenarios": os.path.join(self.prompts_dir, "components_scenarios.json"), # Lưu kịch bản ChatGPT
            "comp_presets": os.path.join(self.prompts_dir, "components_presets.json"),     # Lưu combo ảnh 
            "comp_settings": os.path.join(self.settings_dir, "components_settings.json")   # Lưu cấu hình (như thư mục save)
        }

        # Đảm bảo tạo đủ thư mục vật lý
        os.makedirs(self.db_dir, exist_ok=True)
        os.makedirs(self.prompts_dir, exist_ok=True)
        os.makedirs(self.settings_dir, exist_ok=True)
        os.makedirs(self.profiles_dir, exist_ok=True)
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path, exist_ok=True)

    # =========================================================
    # HÀM LÕI (XỬ LÝ JSON)
    # =========================================================
    def load_json(self, file_key, default_data=None):
        path = self.paths.get(file_key, file_key)
        if os.path.exists(path) and os.path.getsize(path) > 0:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: pass
        return default_data if default_data is not None else {}

    def save_json(self, file_key, data):
        path = self.paths.get(file_key, file_key)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    # =========================================================
    # QUẢN LÝ THƯ MỤC LƯU CHO LUỒNG THÀNH PHẦN (MỚI)
    # =========================================================
    def get_components_save_dir(self, default_dir="F:/Data_Tool_2"):
        """Lấy thư mục xuất video của luồng Thành phần, mặc định là Data_Tool_2"""
        data = self.load_json("comp_settings", {})
        return data.get("save_dir", default_dir)

    def set_components_save_dir(self, save_path):
        """Lưu lại thư mục xuất video khi người dùng chọn trên UI"""
        data = self.load_json("comp_settings", {})
        data["save_dir"] = os.path.normpath(save_path)
        self.save_json("comp_settings", data)

    # =========================================================
    # CÁC HÀM CŨ CHO LUỒNG FRAME (GIỮ NGUYÊN 100%)
    # =========================================================
    def get_sku_metadata(self, sku):
        info_path = os.path.join(self.base_path, sku, "info.json")
        return self.load_json(info_path, None)

    def save_sku_metadata(self, sku, model_path, prod_path, bg_path, product_type_vn):
        sku_dir = os.path.join(self.base_path, sku)
        os.makedirs(sku_dir, exist_ok=True)
        metadata = {
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fixed_model_path": model_path,
            "product_img_path": prod_path,
            "background_path": bg_path,
            "product_type_vn": product_type_vn
        }
        self.save_json(os.path.join(sku_dir, "info.json"), metadata)

    def get_existing_skus(self):
        try:
            if not os.path.exists(self.base_path): return []
            return sorted([d for d in os.listdir(self.base_path) 
                          if os.path.isdir(os.path.join(self.base_path, d))])
        except: return []

    def get_all_profiles(self):
        try:
            profiles = [d for d in os.listdir(self.profiles_dir) 
                        if os.path.isdir(os.path.join(self.profiles_dir, d))]
            if "chrome_auto_profile" in profiles:
                profiles.remove("chrome_auto_profile")
                profiles.insert(0, "chrome_auto_profile")
            return profiles
        except: return []

    def get_safety_account(self, exclude_list=None):
        """Lấy Nick rảnh, tuyệt đối không trùng với các luồng đang chạy"""
        exclude_list = exclude_list or []
        account_db = self.load_json("account")
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Thử 7 nick Free trước
        free_profiles = [f"google_acc_{i}" for i in range(1, 8)]
        for profile in free_profiles:
            if profile in exclude_list: continue
            
            acc_info = account_db.get(profile, {})
            is_empty = (acc_info.get("status") == "empty" and acc_info.get("date") == today)
            if not is_empty:
                return profile

        # Kiểm tra Nick PRO cuối cùng
        pro_profile = "chrome_auto_profile"
        if pro_profile not in exclude_list:
            acc_info = account_db.get(pro_profile, {})
            is_empty = (acc_info.get("status") == "empty" and acc_info.get("date") == today)
            if not is_empty:
                return pro_profile
        
        print("⚠️ [CONFIG] CẢNH BÁO: Không còn nick nào rảnh hoặc còn token cho ngày hôm nay!")
        return None

    def get_safety_chatgpt_account(self, exclude_list=None):
        exclude_list = exclude_list or []
        account_db = self.load_json("chatgpt_account_status")
        today = datetime.now().strftime("%Y-%m-%d")
        
        for i in range(1, 8):
            profile = f"google_acc_{i}"
            if profile in exclude_list: continue
            
            acc_info = account_db.get(profile, {})
            is_empty = (acc_info.get("status") == "empty" and acc_info.get("date") == today)
            if not is_empty:
                return profile
        return None

    def mark_chatgpt_empty(self, profile_name):
        accounts = self.load_json("chatgpt_account_status")
        accounts[profile_name] = {"status": "empty", "date": datetime.now().strftime("%Y-%m-%d")}
        self.save_json("chatgpt_account_status", accounts)
        
    def mark_account_empty(self, profile_name):
        accounts = self.load_json("account")
        accounts[profile_name] = {"status": "empty", "date": datetime.now().strftime("%Y-%m-%d")}
        self.save_json("account", accounts)

    def get_upload_display_name(self, source):
        if isinstance(source, str):
            data = self.load_json(source)
        else:
            data = source
        try:
            return data.get("workflow", {}).get("metadata", {}).get("displayName")
        except Exception:
            return None