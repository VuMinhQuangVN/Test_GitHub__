# import os
# import shutil
# import time
# import re

# class BrowserManager:
#     def __init__(self, profile_name="chrome_auto_profile"):
#         self.profile_name = profile_name
#         # Thư mục lưu trữ các Profile trình duyệt
#         self.base_profiles_dir = os.path.normpath(os.path.join(os.getcwd(), "profiles"))
#         self.profile_dir = os.path.join(self.base_profiles_dir, profile_name)

#     def write_log(self, message):
#         """Hàm ghi log nội bộ cho BrowserManager"""
#         timestamp = time.strftime("%H:%M:%S")
#         print(f"   [{timestamp}] [BROWSER-MGR] {message}")

#     def init_browser(self, p, headless=False, slow_mo=0):
#         """Khởi tạo Chrome 109 cấu hình mượt nhất, lới lỏng tài nguyên mạng"""
#         os.makedirs(self.profile_dir, exist_ok=True)
        
#         # 1. Đường dẫn thực thi của Chrome 109 vừa cài
#         chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
#         if not os.path.exists(chrome_exe):
#             chrome_exe = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

#         # 2. Đặt Port linh hoạt để chạy đa luồng không trùng nhau
#         remote_port = 9222
#         if "acc" in self.profile_name:
#             num_match = re.search(r'\d+', self.profile_name)
#             num = int(num_match.group()) if num_match else 0
#             remote_port = 9230 + num
#         elif "chrome_auto_profile" in self.profile_name:
#             remote_port = 9221

#         # 3. BỘ THAM SỐ TỐI ƯU (SMOOTH & STABLE)
#         args = [
#             '--disable-blink-features=AutomationControlled',
#             '--no-sandbox',
#             '--start-maximized',
#             '--disable-dev-shm-usage',
            
#             # --- CHỐNG XOAY & NGHẼN MẠNG (CỰC QUAN TRỌNG) ---
#             '--disable-quic',                # Tắt HTTP/3 để dùng HTTP/2 ổn định hơn trên Win 11
#             '--disable-http2-grease-settings',
            
#             # --- LÀM SẠCH UI (VÀO VIỆC NHANH HƠN) ---
#             '--disable-session-crashed-bubble', # Tắt bảng 'Restore pages' khi Bot đóng trình duyệt đột ngột
#             '--disable-infobars',               # Tắt thanh 'Chrome is being controlled...'
            
#             # --- TỐI ƯU PHẦN CỨNG ---
#             '--ignore-gpu-blocklist',
#             '--enable-gpu-rasterization',
#             '--enable-native-gpu-memory-buffers',
            
#             # --- TỰ DO TÀI NGUYÊN (GIÚP LOAD TRANG MẠNH NHẤT) ---
#             '--disable-background-timer-throttling',
#             '--disable-backgrounding-occluded-windows',
#             '--disable-renderer-backgrounding',
            
#             # --- THAM SỐ PHỤ ---
#             '--no-first-run',
#             '--no-default-browser-check',
#             '--disable-notifications',
#             '--mute-audio',
            
#             f'--remote-debugging-port={remote_port}'
#         ]

#         # 4. KHỞI CHẠY (KHÔNG FAKE USER AGENT - DÙNG GỐC 109)
#         return p.chromium.launch_persistent_context(
#             user_data_dir=self.profile_dir,
#             executable_path=chrome_exe,
#             headless=headless,
#             slow_mo=slow_mo,
#             args=args,
#             ignore_default_args=["--enable-automation"],
#             no_viewport=True
#         )

#     def cleanup_profile(self):
#         """Dọn dẹp rác cache để máy không bị đứng do nghẽn ổ cứng (Disk I/O)"""
#         trash_folders = ["Cache", "Code Cache", "GPUCache", "Media Cache", "ShaderCache"]
#         for folder in trash_folders:
#             targets = [
#                 os.path.join(self.profile_dir, folder),
#                 os.path.join(self.profile_dir, "Default", folder)
#             ]
#             for target in targets:
#                 if os.path.exists(target):
#                     try: shutil.rmtree(target, ignore_errors=True)
#                     except: pass
#         self.write_log(f"🧹 Dọn dẹp xong: {self.profile_name}")

#     def hard_reset_profile(self):
#         """Xóa sạch hoàn toàn Profile (Chỉ dùng cho ChatGPT Guest hoặc Temp)"""
#         if not any(key in self.profile_name.lower() for key in ["chatgpt", "guest", "temp"]):
#             return
#         self.write_log(f"🧨 Reset Profile: {self.profile_name}...")
#         time.sleep(2) 
#         if os.path.exists(self.profile_dir):
#             try: 
#                 shutil.rmtree(self.profile_dir)
#                 os.makedirs(self.profile_dir, exist_ok=True)
#             except Exception as e: 
#                 self.write_log(f"⚠️ Lỗi kẹt file khi reset: {e}")
import os
import shutil
import time
import re

class BrowserManager:
    def __init__(self, profile_name="chrome_auto_profile"):
        self.profile_name = profile_name
        self.base_profiles_dir = os.path.normpath(os.path.join(os.getcwd(), "profiles"))
        self.profile_dir = os.path.join(self.base_profiles_dir, profile_name)

    def write_log(self, message):
        """Hàm ghi log nội bộ cho BrowserManager"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"   [{timestamp}] [BROWSER-MGR] {message}")

    def init_browser(self, p, headless=False, slow_mo=0):
        """Khởi tạo Chrome với cấu hình ẩn danh (Stealth) và ưu tiên độ mượt"""
        os.makedirs(self.profile_dir, exist_ok=True)
        
        chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if not os.path.exists(chrome_exe):
            chrome_exe = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

        remote_port = 9222
        if "acc" in self.profile_name:
            num_match = re.search(r'\d+', self.profile_name)
            num = int(num_match.group()) if num_match else 0
            remote_port = 9230 + num
        elif "chrome_auto_profile" in self.profile_name:
            remote_port = 9221

        # --- BỘ THAM SỐ CHUẨN LÁCH QUÉT BOT & TỐI ƯU MƯỢT MÀ ---
        args = [
            # 1. QUAN TRỌNG NHẤT: Lách các bộ quét Automation của Google/OpenAI
            '--disable-blink-features=AutomationControlled', # Xóa cờ navigator.webdriver
            '--no-first-run',
            '--no-default-browser-check',
            '--password-store=basic',          # Tránh hỏi mật khẩu hệ thống
            '--use-mock-keychain',             # Giả lập keychain để tránh popup OS
            
            # 2. LÀM SẠCH UI (Vào việc nhanh, ko vướng popup)
            '--disable-infobars',               # Tắt thanh 'Chrome is being controlled...'
            '--disable-session-crashed-bubble', # Tắt bảng 'Restore pages'
            '--disable-notifications',          # Chặn popup thông báo từ web
            '--start-maximized',
            '--mute-audio',
            
            # 3. TỐI ƯU HIỆU NĂNG (Giữ lại GPU để mượt nhưng chặn rác)
            '--disable-dev-shm-usage',          # Ép dùng RAM thay vì bộ nhớ đệm đĩa
            '--disable-gpu-program-cache',      # Tránh lỗi cache shader khi chạy đa luồng
            '--disable-background-networking',  # Tắt các tiến trình cập nhật ngầm ngốn băng thông
            
            f'--remote-debugging-port={remote_port}'
        ]

        # 4. KHỞI CHẠY PERSISTENT CONTEXT
        context = p.chromium.launch_persistent_context(
            user_data_dir=self.profile_dir,
            executable_path=chrome_exe,
            headless=headless,
            slow_mo=slow_mo,
            args=args,
            # Loại bỏ cờ --enable-automation mặc định của Playwright (Rất quan trọng)
            ignore_default_args=["--enable-automation"], 
            no_viewport=True
        )

        # Mẹo nhỏ: Tiêm thêm đoạn mã Javascript để xóa hoàn toàn dấu vết Playwright
        # Điều này giúp bạn vượt qua các bài kiểm tra Bot nâng cao
        page = context.pages[0]
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        return context

    def cleanup_profile(self):
        """Hút mỡ Profile nhẹ nhàng (Tránh xóa nhầm GPUCache gây lag)"""
        trash_folders = ["Cache", "Code Cache", "Media Cache"]
        for folder in trash_folders:
            targets = [
                os.path.join(self.profile_dir, folder),
                os.path.join(self.profile_dir, "Default", folder)
            ]
            for target in targets:
                if os.path.exists(target):
                    try: shutil.rmtree(target, ignore_errors=True)
                    except: pass
        self.write_log(f"🧹 Dọn dẹp cache xong cho: {self.profile_name}")

    def hard_reset_profile(self):
        """Xóa sạch hoàn toàn (Chỉ dùng cho Guest)"""
        if not any(key in self.profile_name.lower() for key in ["chatgpt", "guest", "temp"]):
            return
        self.write_log(f"🧨 Reset Profile: {self.profile_name}...")
        time.sleep(2) 
        if os.path.exists(self.profile_dir):
            try: 
                shutil.rmtree(self.profile_dir)
                os.makedirs(self.profile_dir, exist_ok=True)
            except Exception as e: 
                self.write_log(f"⚠️ Lỗi reset: {e}")