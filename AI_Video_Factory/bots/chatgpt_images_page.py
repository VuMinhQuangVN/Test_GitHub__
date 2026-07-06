# import time, os, re, datetime, json
# from bots.base_page import BasePage

# class ChatGPTImagesPage(BasePage):
#     def __init__(self, page):
#         super().__init__(page)
#         self.url = "https://chatgpt.com/"
        
#         self.locators = {
#             "prompt_box": "#prompt-textarea",
#             "btn_plus": "button[data-testid='composer-plus-btn']",
#             "menu_item_upload": "//div[contains(text(), 'Thêm ảnh và tệp')] | //div[contains(text(), 'Add photos')]",
#             "btn_send": "button[data-testid='send-button']",
#             "btn_stop": "button[aria-label='Stop generating']",
#             "btn_idle_state": "button[aria-label='Start Voice'], [data-testid='composer-speech-button']",
            
#             # --- SELECTOR GLOBAL THEO CƠ CHẾ MỚI ---
#             "generated_images": "div[role='button'] img[alt*='Generated image'], div[role='button'] img[alt*='Ảnh đã tạo']",
#             "last_markdown": "div.markdown",
#             "btn_download_editor": "button[aria-label='Tải xuống'], button[aria-label='Download'], button[aria-label='Lưu'], button[aria-label='Save']",
            
#             "btn_close_dialog": "button[data-testid='close-button']",
#             "dialog_overlay": "div[role='dialog']"
#         }

#     def write_log(self, step, message, status="INFO"):
#         ts = datetime.datetime.now().strftime("%H:%M:%S")
#         print(f"[{ts}] [{status}] [Step {step}] {message}")

#     def highlight(self, element, color="red"):
#         """Khoanh vùng phần tử để theo dõi trực tiếp"""
#         try:
#             element.scroll_into_view_if_needed()
#             element.evaluate(f"el => el.style.outline = '4px solid {color}'")
#             return element
#         except: return None

#     def navigate(self):
#         self.write_log(0, "🌐 Truy cập ChatGPT...")
#         self.page.goto(self.url, wait_until="domcontentloaded")
#         time.sleep(4)
#         self.handle_popups()

#     def handle_popups(self):
#         try:
#             close_btn = self.page.locator(self.locators["btn_close_dialog"]).first
#             if close_btn.is_visible(timeout=1000):
#                 close_btn.click(force=True)
#                 return
#             if self.page.locator(self.locators["dialog_overlay"]).first.is_visible(timeout=500):
#                 self.page.mouse.click(10, 10)
#         except: pass

#     def upload_references(self, img_list):
#         """Nạp ảnh tham chiếu qua Menu UI"""
#         try:
#             self.handle_popups()
#             valid_paths = [os.path.normpath(p) for p in img_list if os.path.exists(p)]
#             if valid_paths:
#                 self.write_log(1, f"📤 Nạp {len(valid_paths)} ảnh tham chiếu...")
#                 self.page.locator(self.locators["btn_plus"]).click(force=True)
#                 time.sleep(1)
#                 with self.page.expect_file_chooser() as fc_info:
#                     self.page.locator(self.locators["menu_item_upload"]).first.click(force=True)
#                 fc_info.value.set_files(valid_paths)
#                 self.write_log(1, "⏳ Chờ ChatGPT nạp ảnh (12s)...", "WAIT")
#                 time.sleep(12) 
#                 return True
#             return False
#         except Exception as e:
#             self.write_log(1, f"❌ Lỗi upload: {e}", "FAIL")
#             return False

#     def generate_step(self, prompt, save_path, step_label):
#         """Hàm thực thi chính cho mỗi Shot"""
#         try:
#             self.handle_popups()
#             strict_prompt = f"{prompt} -- Create EXACTLY ONE image. No choices."
#             self.write_log(step_label, "✍️ Gửi lệnh vẽ...")
            
#             box = self.page.locator(self.locators["prompt_box"])
#             box.fill(strict_prompt)
            
#             # Đợi nút Gửi sáng lên
#             send_btn = self.page.locator(self.locators["btn_send"])
#             start_wait = time.time()
#             while time.time() - start_wait < 60:
#                 if send_btn.is_enabled(): break
#                 time.sleep(2)
            
#             send_btn.click(force=True)

#             # --- CHỜ RENDER XONG (LOGIC GLOBAL SCAN) ---
#             status = self._wait_for_render_done(step_label)
            
#             if status == "LIMIT_REACHED":
#                 return "OUT_OF_CREDIT"
            
#             if status is True:
#                 # --- TẢI ẢNH (LOGIC GLOBAL SCAN) ---
#                 return self._download_last_assistant_image(save_path, step_label)
            
#             return None
#         except Exception as e:
#             self.write_log(step_label, f"❌ Lỗi: {e}", "FAIL")
#             return None

#     # =========================================================
#     # LOGIC GLOBAL SCAN CỦA BẠN - ĐÃ ĐỒNG BỘ VÀO CLASS
#     # =========================================================
#     def _wait_for_render_done(self, step_label, timeout=300):
#         """Theo dõi toàn trang tới khi phát hiện ảnh mới xuất hiện"""
#         start_time = time.time()
#         self.write_log(step_label, "🎨 AI đang vẽ (DALL-E)...", "WAIT")

#         # Đếm số lượng ảnh hiện có trước khi vẽ
#         initial_count = self.page.locator(self.locators["generated_images"]).count()
#         self.write_log(step_label, f"📸 Ban đầu có {initial_count} ảnh")

#         while time.time() - start_time < timeout:
#             self.handle_popups()

#             # --- CHECK LIMIT ---
#             try:
#                 markdowns = self.page.locator(self.locators["last_markdown"])
#                 if markdowns.count() > 0:
#                     content = markdowns.last.inner_text().lower()
#                     if "hit the free plan limit" in content or "limit resets in" in content:
#                         self.write_log(step_label, "🛑 Hết lượt tạo ảnh!", "FAIL")
#                         return "LIMIT_REACHED"
#             except: pass

#             # --- CHECK AI STATE ---
#             try:
#                 is_writing = self.page.locator(self.locators["btn_stop"]).is_visible(timeout=1000)
#             except: is_writing = False

#             try:
#                 is_idle = self.page.locator(self.locators["btn_idle_state"]).is_visible(timeout=1000)
#             except: is_idle = False

#             # --- AI FINISHED ---
#             if not is_writing and is_idle:
#                 self.write_log(step_label, "✅ AI đã ngừng viết. Quét ảnh...")
#                 try:
#                     imgs = self.page.locator(self.locators["generated_images"])
#                     current_count = imgs.count()

#                     # Nếu số lượng ảnh tăng lên -> Có ảnh mới
#                     if current_count > initial_count:
#                         newest_img = imgs.nth(current_count - 1)
#                         newest_img.wait_for(state="visible", timeout=15000)
                        
#                         self.highlight(newest_img, color="green")
#                         self.write_log(step_label, f"✨ ẢNH ĐÃ RENDER XONG! (Tổng: {current_count})", "OK")
#                         time.sleep(3)
#                         return True
#                     else:
#                         self.write_log(step_label, f"⌛ Đang đợi ảnh hiện diện (Hiện tại vẫn {current_count})...", "WAIT")
#                 except Exception as e:
#                     self.write_log(step_label, f"⌛ Chưa bắt được ảnh: {e}", "WAIT")

#             time.sleep(5)
#         self.write_log(step_label, "❌ Timeout render ảnh", "FAIL")
#         return False

#     def _download_last_assistant_image(self, save_path, step_label):
#         """Download ảnh mới nhất bằng cách scan Global"""
#         try:
#             self.write_log(step_label, "🔍 Đang tìm ảnh mới nhất...")
            
#             imgs = self.page.locator(self.locators["generated_images"])
#             img_count = imgs.count()

#             self.write_log(step_label, f"🖼️ Có tổng {img_count} ảnh trên trang")
#             if img_count == 0:
#                 raise Exception("Không tìm thấy ảnh generated")

#             # Lấy ảnh cuối cùng (Mới nhất)
#             target_click = imgs.nth(img_count - 1)
#             target_click.wait_for(state="visible", timeout=15000)

#             self.highlight(target_click, color="blue")
#             self.write_log(step_label, "🖱️ Click mở viewer...")
#             target_click.click(force=True)

#             # Chờ Viewer
#             time.sleep(5)

#             # Download button
#             dl_btn = self.page.locator(self.locators["btn_download_editor"]).first
#             dl_btn.wait_for(state="visible", timeout=30000)
#             self.highlight(dl_btn, color="red")

#             self.write_log(step_label, "📥 Đang tải ảnh...")
#             with self.page.expect_download(timeout=120000) as d_info:
#                 dl_btn.click(force=True)
            
#             download = d_info.value
#             download.save_as(save_path)
#             self.write_log(step_label, f"💾 ĐÃ LƯU: {os.path.basename(save_path)}", "OK")

#             self.page.keyboard.press("Escape")
#             time.sleep(2)
#             return save_path

#         except Exception as e:
#             self.write_log(step_label, f"❌ Lỗi tải ảnh: {e}", "FAIL")
#             try: self.page.keyboard.press("Escape")
#             except: pass
#             return None
import time, os, re, datetime, json
from bots.base_page import BasePage

class ChatGPTImagesPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.url = "https://chatgpt.com/"
        
        self.locators = {
            "prompt_box": "#prompt-textarea",
            "btn_plus": "button[data-testid='composer-plus-btn']",
            "menu_item_upload": "//div[contains(text(), 'Thêm ảnh và tệp')] | //div[contains(text(), 'Add photos')]",
            "btn_send": "button[data-testid='send-button']",
            "btn_stop": "button[aria-label='Stop generating']",
            "btn_idle_state": "button[aria-label='Start Voice'], [data-testid='composer-speech-button']",
            "generated_images": "div[role='button'] img[alt*='Generated image'], div[role='button'] img[alt*='Ảnh đã tạo']",
            "last_markdown": "div.markdown",
            "btn_download_editor": "button[aria-label='Tải xuống'], button[aria-label='Download'], button[aria-label='Lưu'], button[aria-label='Save']",
            "btn_close_dialog": "button[data-testid='close-button']",
            "dialog_overlay": "div[role='dialog']"
        }

    def write_log(self, step, message, status="INFO"):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] [{status}] [Step {step}] {message}")

    def highlight(self, element, color="red"):
        try:
            element.scroll_into_view_if_needed()
            element.evaluate(f"el => el.style.outline = '4px solid {color}'")
            return element
        except: return None

    def navigate(self):
        self.write_log(0, "🌐 Truy cập ChatGPT...")
        self.page.goto(self.url, wait_until="domcontentloaded")
        time.sleep(4)
        self.handle_popups()

    def handle_popups(self):
        try:
            close_btn = self.page.get_by_test_id("close-button").first
            if close_btn.is_visible(timeout=1000):
                close_btn.click(force=True)
                return
            if self.page.locator(self.locators["dialog_overlay"]).first.is_visible(timeout=500):
                self.page.mouse.click(10, 10)
        except: pass

    def _check_upload_error(self):
        """Quét xem có thông báo đỏ chặn upload không"""
        error_messages = [
            "You may only upload 1 files at a time",
            "only upload 1 files",
            "Unable to upload"
        ]
        for msg in error_messages:
            # Tìm bất kỳ element nào chứa đoạn text lỗi trên
            try:
                # Dùng selector text của Playwright, không cần quan tâm class
                error_el = self.page.get_by_text(msg, exact=False)
                if error_el.is_visible(timeout=2000): # Chỉ đợi 2s
                    return True
            except:
                continue
        return False

    def upload_references(self, img_list):
        """Nạp ảnh tham chiếu qua Menu UI"""
        try:
            time.sleep(7)
            self.handle_popups()
            valid_paths = [os.path.normpath(p) for p in img_list if os.path.exists(p)]
            if valid_paths:
                self.write_log(1, f"📤 Nạp {len(valid_paths)} ảnh qua Menu...")
                self.page.locator(self.locators["btn_plus"]).click(force=True)
                time.sleep(1)
                with self.page.expect_file_chooser() as fc_info:
                    self.page.locator(self.locators["menu_item_upload"]).first.click(force=True)
                fc_info.value.set_files(valid_paths)
                time.sleep(2) # Đợi 2s để thông báo đỏ kịp hiện ra
                if self._check_upload_error():
                    self.write_log(1, "🛑 ChatGPT chặn upload (Limit 1 file)!", "FAIL")
                    return "LIMIT_REACHED" # Trả về tín hiệu để Worker biết mà đổi nick
                    
                self.write_log(1, "⌛ Đang chờ ChatGPT nạp ảnh (12s)...", "WAIT")
                time.sleep(12) 
                return True
            return False
        except Exception as e:
            self.write_log(1, f"❌ Lỗi upload: {e}", "FAIL")
            return False

    def generate_step(self, prompt, save_path, step_label):
        """Hàm thực thi Shot: Gửi lệnh -> Check Limit -> Tải ảnh"""
        try:
            self.handle_popups()
            # Ép AI chỉ ra 1 kết quả để tránh bắt người dùng chọn
            strict_prompt = f"{prompt} -- Generate only ONE final image.\nDo not create multiple variations.\nSingle output only."
            self.write_log(step_label, "✍️ Gửi lệnh vẽ...")
            
            box = self.page.locator(self.locators["prompt_box"])
            box.fill(strict_prompt)
            time.sleep(2)
            send_btn = self.page.locator(self.locators["btn_send"])
            start_wait = time.time()
            while time.time() - start_wait < 60:
                if send_btn.is_enabled(): break
                time.sleep(2)
            
            send_btn.click(force=True)

            # Đợi render và check hết lượt
            status = self._wait_for_render_done(step_label)
            
            if status == "LIMIT_REACHED":
                return "OUT_OF_CREDIT"
            
            if status is True:
                return self._download_last_assistant_image(save_path, step_label)
            
            return None
        except Exception as e:
            self.write_log(step_label, f"❌ Lỗi: {e}", "FAIL")
            return None

    def _wait_for_render_done(self, step_label, timeout=300):
        """Logic quét Global phát hiện ảnh mới và Check Limit"""
        start_time = time.time()
        self.write_log(step_label, "🎨 AI đang vẽ (DALL-E)...", "WAIT")

        initial_count = self.page.locator(self.locators["generated_images"]).count()

        while time.time() - start_time < timeout:
            self.handle_popups()

            # --- 1. KIỂM TRA LIMIT NGAY TRONG TEXT PHẢN HỒI ---
            try:
                markdowns = self.page.locator(self.locators["last_markdown"])
                if markdowns.count() > 0:
                    content = markdowns.last.inner_text().lower()
                    if "hit the free plan limit" in content or "limit resets in" in content:
                        self.write_log(step_label, "🛑 ChatGPT báo hết lượt tạo ảnh!", "FAIL")
                        return "LIMIT_REACHED"
            except: pass

            # --- 2. CHECK TRẠNG THÁI XONG ---
            try:
                is_writing = self.page.locator(self.locators["btn_stop"]).is_visible(timeout=1000)
                is_idle = self.page.locator(self.locators["btn_idle_state"]).is_visible(timeout=1000)
            except: is_writing, is_idle = False, False

            if not is_writing and is_idle:
                try:
                    imgs = self.page.locator(self.locators["generated_images"])
                    current_count = imgs.count()
                    if current_count > initial_count:
                        newest_img = imgs.nth(current_count - 1)
                        newest_img.wait_for(state="visible", timeout=15000)
                        self.highlight(newest_img, color="green")
                        self.write_log(step_label, "✨ ẢNH ĐÃ RENDER XONG!", "OK")
                        time.sleep(3)
                        return True
                except: pass

            time.sleep(5)
        return False

    def _download_last_assistant_image(self, save_path, step_label):
        """Tải ảnh chuẩn xác theo Global Scan"""
        try:
            self.write_log(step_label, "🔍 Tìm ảnh mới nhất...")
            imgs = self.page.locator(self.locators["generated_images"])
            img_count = imgs.count()

            if img_count == 0: raise Exception("Không tìm thấy ảnh")

            target_click = imgs.nth(img_count - 1)
            target_click.wait_for(state="visible", timeout=15000)
            self.highlight(target_click, color="blue")
            
            self.write_log(step_label, "🖱️ Mở trình xem ảnh...")
            target_click.click(force=True)
            time.sleep(6) # Đợi viewer

            dl_btn = self.page.locator(self.locators["btn_download_editor"]).first
            dl_btn.wait_for(state="visible", timeout=30000)
            self.highlight(dl_btn, color="red")

            self.write_log(step_label, "📥 Đang tải file gốc...")
            with self.page.expect_download(timeout=120000) as d_info:
                dl_btn.click(force=True)
            
            d_info.value.save_as(save_path)
            self.write_log(step_label, f"💾 ĐÃ LƯU: {os.path.basename(save_path)}", "OK")
            self.page.keyboard.press("Escape")
            time.sleep(2)
            return save_path
        except Exception as e:
            self.write_log(step_label, f"❌ Lỗi tải ảnh: {e}", "FAIL")
            self.page.keyboard.press("Escape")
            return None