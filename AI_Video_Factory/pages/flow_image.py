# -*- coding: utf-8 -*-
# pages/flow_image.py
import time
import os
import datetime
import re
from pages.base_page import BasePage
from core.config_manager import ConfigManager # Import thêm config manager

class FlowImagePage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.url = "https://labs.google/fx/vi/tools/flow"
        self.config_manager = ConfigManager() # Khởi tạo cấu hình
        
        self.locators = {
            # --- POPUPS ---
            "btn_agree": "button:has-text('Tôi đồng ý'), button.khyiiG",
            "btn_get_started": "button:has-text('Bắt đầu'), button:has-text('Get started'), button.bkfetv",

            # --- DỰ ÁN & UPLOAD ---
            "btn_new_project": "button:has(i:text-is('add_2')):has-text('Dự án mới'), button:has-text('Dự án mới'), button:has-text('New project')",
            "btn_top_plus": "button:has(i:text('add')), button:has-text('Thêm nội dung')",
            "btn_upload_option": "button[role='menuitem']:has(i:text('upload'))",
            "upload_progress": "//div[contains(text(), '%')]",
            
            # --- CẤU HÌNH IMAGE MODE ---
            "btn_mode_selector": "button:has(i:text-is('crop_9_16')), button:has(i:text-is('crop_portrait')), button:has(i:text-is('crop_16_9')), button:has(i:text-is('crop_landscape'))",
            "tab_image": "button[id$='trigger-IMAGE']",
            "tab_9_16": "button[id$='trigger-PORTRAIT']",
            "tab_x2": "button[id$='trigger-2']", 
            "model_selector_btn": "button:has(i:text-is('arrow_drop_down')):visible",
            "menu_items": "div[role='menuitem'], div[role='option']",

            # --- THAM CHIẾU ---
            "btn_add_ref_bottom": "button:has(i:text('add_2'))",
            "library_dialog": "//div[contains(@role, 'dialog')]",
            "file_in_library": "//div[contains(@role, 'dialog')]//div[text()='{}']",
            "btn_add_to_prompt": "button:has-text('Thêm vào câu lệnh'), button:has-text('Add to prompt')", 

            # --- TẠO & TẢI ---
            "input_prompt": "div[data-slate-editor='true']",
            "btn_generate": "button:has(i:text-is('arrow_forward')):visible",
            "result_thumbnail": "img[alt='Hình ảnh được tạo']",
            "btn_download_header": "button:has-text('Tải xuống'), button:has-text('Download')",
            "option_2k": "button[role='menuitem']:has-text('2K')",
            "error_banner": "//div[contains(text(), 'Không thể tạo') or contains(text(), 'failed')]",
        }

    def write_log(self, message):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"   [FLOW-IMAGE] [{ts}]: {message}")

    def navigate(self):
        self.write_log(f"🌐 Truy cập Google Flow...")
        self.page.goto(self.url, wait_until="domcontentloaded")
        time.sleep(2)
        self.handle_popups()

    def handle_popups(self):
        try:
            if self.page.locator(self.locators["btn_agree"]).is_visible(timeout=2000):
                self.write_log("⚠️ Chấp nhận điều khoản sử dụng...")
                self.page.locator(self.locators["btn_agree"]).click(force=True)
                time.sleep(1)

            if self.page.locator(self.locators["btn_get_started"]).is_visible(timeout=2000):
                self.write_log("✨ Đóng bảng thông báo 'Share your creations'...")
                self.page.locator(self.locators["btn_get_started"]).click(force=True)
                time.sleep(1)
        except:
            pass

    # === UPDATE MỚI: BATCH UPLOAD HOÀN TOÀN TỰ ĐỘNG BẰNG INTERCEPTION ===
    def upload_references_batch(self, image_paths: list):
        valid_paths = [os.path.normpath(p) for p in image_paths if p and os.path.exists(p)]
        if not valid_paths:
            self.write_log("❌ Lỗi: Danh sách ảnh tải lên trống hoặc không tìm thấy file!")
            return False
            
        self.write_log(f"📤 Đang chuẩn bị tải lên đồng loạt {len(valid_paths)} ảnh mẫu...")
        
        pending_to_catch = [os.path.basename(p) for p in valid_paths]
        captured_responses = []

        def handle_response(res):
            if "uploadImage" in res.url and res.status == 200:
                try: captured_responses.append(res.json())
                except: pass

        self.page.on("response", handle_response)
        
        try:
            # 1. Bật bảng Thêm nội dung (+)
            self.page.locator(self.locators["btn_top_plus"]).first.click(force=True)
            self.page.wait_for_timeout(1000)
            
            # 2. Gọi File Chooser
            with self.page.expect_file_chooser(timeout=30000) as fc_info:
                self.page.locator(self.locators["btn_upload_option"]).first.click(force=True)
                
            # 3. Đẩy đồng loạt danh sách đường dẫn
            fc_info.value.set_files(valid_paths)
            self.write_log("⏳ Đang theo dõi tiến trình upload từ máy chủ...")
            
            start_wait = time.time()
            while time.time() - start_wait < 90: # Timeout 90s
                for data in captured_responses[:]:
                    json_display_name = self.config_manager.get_upload_display_name(data)
                    if json_display_name in pending_to_catch:
                        pending_to_catch.remove(json_display_name)
                        captured_responses.remove(data)
                        self.write_log(f"   ✅ Đã tải lên thành công: {json_display_name}")
                
                if not pending_to_catch:
                    self.write_log("🚀 Toàn bộ ảnh mẫu đã được upload xong!")
                    return True
                self.page.wait_for_timeout(2000)
            else:
                self.write_log(f"⚠️ Hết thời gian chờ, thiếu file: {pending_to_catch}", "WARN")
                return False
        finally:
            self.page.remove_listener("response", handle_response)

    def _configure_settings(self):
        self.write_log("⚙️ Thiết lập Image Mode (9:16, x2, Pro)")
        try:
            if not self.page.locator(self.locators["tab_image"]).first.is_visible(timeout=1000):
                self.write_log("   🔍 Đang mở bảng chọn Chế độ/Cài đặt...")
                self.page.locator(self.locators["btn_mode_selector"]).first.click(force=True)
                self.page.wait_for_timeout(1500)

            btn_img_tab = self.page.locator(self.locators["tab_image"]).first
            btn_img_tab.click(force=True)
            self.page.wait_for_timeout(800)

            for key in ["tab_9_16", "tab_x2"]:
                loc = self.page.locator(self.locators[key]).first
                loc.click(force=True)
                self.page.wait_for_timeout(500)

            model_btn = self.page.locator(self.locators["model_selector_btn"]).last
            model_btn.click(force=True)
            self.page.wait_for_timeout(1000)
            
            options = self.page.locator(self.locators["menu_items"]).all()
            for opt in options:
                txt = opt.inner_text()
                if "Pro" in txt or "Banana" in txt:
                    opt.click(force=True)
                    self.write_log(f"   ✨ Đã chọn model: {txt.strip()}")
                    break
            
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(1000)
        except Exception as e:
            self.write_log(f"   ⚠️ Lỗi cấu hình: {e}")

    def _select_reference_from_library(self, filename: str):
        self.write_log(f"🎯 Tìm và chọn tham chiếu: {filename}")
        try:
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(500)

            dialog = self.page.locator(self.locators["library_dialog"])
            
            if not dialog.is_visible(timeout=500):
                plus_btn = self.page.locator(self.locators["btn_add_ref_bottom"]).first
                plus_btn.scroll_into_view_if_needed()
                plus_btn.click(force=True)
                try: dialog.wait_for(state="visible", timeout=5000)
                except: plus_btn.click(force=True)

            target_selector = self.locators["file_in_library"].format(filename)
            self.page.wait_for_selector(target_selector, state="visible", timeout=60000)
            
            self.page.locator(target_selector).first.click(force=True)
            self.page.wait_for_timeout(800)
            
            btn_confirm = self.page.locator(self.locators["btn_add_to_prompt"])
            if btn_confirm.is_visible(timeout=3000):
                btn_confirm.click(force=True)
                self.write_log(f"   ✅ Đã click 'Thêm vào câu lệnh'")
            
            self.page.wait_for_timeout(1000)
            self.write_log(f"   ✅ Đã chọn thành công: {filename}")
            return True
        except Exception as e:
            self.write_log(f"   ⚠️ Lỗi chọn ảnh {filename}: {e}")
            self.page.keyboard.press("Escape")
            return False

    def get_current_thumb_count(self):
        return self.page.locator(self.locators["result_thumbnail"]).count()

    def monitor_render(self, initial_count, batch_limit=2):
        self.write_log(f"⏳ Đang đợi Render (x{batch_limit})...")
        start = time.time()
        has_started = False
        while time.time() - start < 450:
            if self.page.locator(self.locators["error_banner"]).is_visible(timeout=500):
                self.write_log("❌ Google từ chối vẽ prompt này.")
                return 0

            progress = self.page.locator("//div[contains(., '%')]").last
            if progress.is_visible(timeout=500):
                has_started = True
            elif has_started:
                self.page.wait_for_timeout(5000) 
                new_total = self.get_current_thumb_count()
                new_count = new_total - initial_count
                return min(max(0, new_count), batch_limit)
            time.sleep(4)
        return 0

    def download_batch(self, count, save_dir, sku, shot_type):
        downloaded_paths = []
        for i in range(count):
            try:
                self.write_log(f"📥 Tải ảnh mới vị trí {i+1}...")
                thumb = self.page.locator(self.locators["result_thumbnail"]).nth(i)
                thumb.wait_for(state="visible", timeout=10000)
                thumb.click(force=True)
                self.page.wait_for_timeout(3000)

                self.page.locator(self.locators["btn_download_header"]).click()
                with self.page.expect_download(timeout=60000) as dl_info:
                    self.page.locator(self.locators["option_2k"]).click()
                
                img_folder = os.path.join(save_dir, "base_image")
                os.makedirs(img_folder, exist_ok=True)
                
                timestamp = datetime.datetime.now().strftime('%H%M%S')
                save_path = os.path.join(img_folder, f"base_{sku}_{shot_type}_{timestamp}_{i}.jpg")
                dl_info.value.save_as(save_path)
                downloaded_paths.append(save_path)
                
                self.page.keyboard.press("Escape")
                self.page.wait_for_timeout(1000)
            except Exception as e:
                self.write_log(f"⚠️ Lỗi tải ảnh index {i}: {e}")
                self.page.keyboard.press("Escape")
        return downloaded_paths