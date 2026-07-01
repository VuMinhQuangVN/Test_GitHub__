#-*- coding: utf-8 -*-
import time, os, datetime, re, json, random
from pages.base_page import BasePage
from core.config_manager import ConfigManager


class FlowPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.url = "https://labs.google/fx/vi/tools/flow"
        self.config_manager = ConfigManager() 
        self.locators = {
            "btn_avatar": "//button[.//img[contains(@alt, 'hồ sơ')]]",
            "credit_info": "//span[contains(., 'Tín dụng')] | //a[contains(., 'Tín dụng')]",
            "btn_new_project": "button:has(i:text-is('add_2')):has-text('Dự án mới'), button:has-text('Dự án mới'), button:has-text('New project')",
            "btn_plus_add": "button[id^='radix-']:has(i:text-is('add'))",
            "btn_upload_option": "button[role='menuitem']:has(i:text-is('upload'))",
            "upload_percentage": "//div[has(i:text-is('image'))]//div[contains(text(), '%')]",
            "btn_config_main": "button[id^='radix-']:has(i:text-is('crop_9_16'))",
            "btn_add_to_prompt": "button:has-text('Thêm vào câu lệnh'), button:has-text('Add to prompt')",
            "rendering_percentage": "//div[contains(., '%') and contains(@class, 'sc-')]",
            "first_video_thumb": "button:has(video), button:has(img[alt*='video'])",
            "error_msg": "//div[contains(., 'Không thành công') or contains(., 'failed')]",
            "btn_download_trigger": "button:has-text('Tải xuống'), button:has-text('Download')",
            "res_720p": "button[role='menuitem']:has-text('720p')",
            "res_1080p": "button[role='menuitem']:has-text('1080p')"
        }

    def write_flow_log(self, step, message, status="INFO"):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{status}] [Step {step}] {message}")

    def action_click(self, selector, step, desc, timeout=15000):
        try:
            target = self.page.locator(selector).first
            target.scroll_into_view_if_needed()
            target.evaluate("el => el.style.outline = '3px solid red'")
            time.sleep(0.5) 
            target.click(timeout=timeout, force=True)
            self.write_flow_log(step, f"Thành công: {desc}", "OK")
            return True
        except:
            self.write_flow_log(step, f"Thất bại: {desc}", "FAIL")
            return False

    def check_credits(self):
        try:
            self.write_flow_log("PRE-CHECK", "Đang kiểm tra Tín dụng AI...")
            self.page.locator(self.locators["btn_avatar"]).first.click()
            time.sleep(2)
            credit_text = self.page.locator(self.locators["credit_info"]).first.inner_text()
            tokens = int(re.search(r'(\d+)', credit_text).group(1)) if re.search(r'(\d+)', credit_text) else 0
            self.write_flow_log("PRE-CHECK", f"Tín dụng còn lại: {tokens}", "INFO")
            self.page.mouse.click(200, 300)
            return tokens > 0
        except: return True

    def navigate(self):
        self.page.goto(self.url, wait_until="domcontentloaded")
        time.sleep(2)
        try: self.page.get_by_role("button", name=re.compile(r"Bắt đầu|Get started", re.I)).click(timeout=3000)
        except: pass

    def create_video(self, image_path, prompt_text, save_dir, profile_name, sku, mode="frames", model_type="Lite", batch_id=None):
        if not self.check_credits(): return "OUT_OF_CREDIT"
        img_list = [os.path.normpath(p) for p in image_path] if isinstance(image_path, list) else [os.path.normpath(image_path)]
        
        # --- PHẦN IN DANH SÁCH ẢNH NGAY ĐẦU ---
        self.write_flow_log("0", f"📋 Bắt đầu quy trình. Tổng số ảnh: {len(img_list)}")
        list_name_image = [str(os.path.basename(p)) for p in img_list]
        for i, p in enumerate(img_list, 1):
            self.write_flow_log("0", f"   📸 Ảnh {i}: {os.path.basename(p)}")

        # Dọn dẹp thư mục debug_uploads
        debug_folder = "debug_uploads"
        if os.path.exists(debug_folder):
            files_deleted = 0
            for f in os.listdir(debug_folder):
                if f.endswith(".json"):
                    try:
                        os.remove(os.path.join(debug_folder, f))
                        files_deleted += 1
                    except Exception: pass
            self.write_flow_log("0", f"🧹 Đã xóa {files_deleted} file JSON cũ trong '{debug_folder}'")
        else:
            os.makedirs(debug_folder, exist_ok=True)
            self.write_flow_log("0", f"📁 Đã tạo mới thư mục '{debug_folder}'")
        # -------------------------------------

        try:
            self.action_click(self.locators["btn_new_project"], "1", "Dự án mới")
            time.sleep(5) 
            self.action_click(self.locators["btn_plus_add"], "2.1", "Mở menu Add")
            

            pending_to_catch = list_name_image.copy() # Tạo bản sao danh sách tên ảnh cần bắt
            captured_responses = []
            # def handle_response(res):
            #     if "uploadImage" in res.url and res.status == 200:
            #         try:
            #             data = res.json()
            #             m_id = data.get("media", {}).get("name")
            #             if m_id:
            #                 file_path = os.path.join(debug_folder, f"res_{m_id}.json")
            #                 with open(file_path, "w", encoding="utf-8") as f:
            #                     json.dump(data, f, indent=4, ensure_ascii=False)
            #                 # Log nhẹ để biết có file mới
            #                 # self.write_flow_log("DEBUG", f"📩 Đã nhận response cho ID: {m_id}")
            #         except Exception: pass
            def handle_response(res):
                if "uploadImage" in res.url and res.status == 200:
                    try:
                        data = res.json()
                        # Lưu thẳng dictionary vào list trong RAM, không ghi file nữa
                        captured_responses.append(data)
                    except: pass


            self.page.on("response", handle_response)

            try:
                # 2. Kích hoạt upload
                with self.page.expect_file_chooser() as fc:
                    self.action_click(self.locators["btn_upload_option"], "2.2", "Chọn Tải lên")
                fc.value.set_files(img_list)

                # 3. Vòng lặp kiểm tra thông minh (Thay thế cho sleep 60s)
                self.write_flow_log("2.3", f"⏳ Đang đợi bắt {len(pending_to_catch)} file JSON...")
                
                start_wait = time.time()
                while time.time() - start_wait < 60: # Timeout tối đa 60s
                    # Quét thư mục debug_uploads để tìm file JSON mới
                    # for file_name in os.listdir(debug_folder):
                    # Duyệt danh sách các response đã bắt được trong RAM
                    for data in captured_responses[:]: # Dùng [:] để tạo bản sao khi duyệt cho an toàn
                        # if not file_name.endswith(".json"): continue
                        
                        # file_path = os.path.join(debug_folder, file_name)
                        # Dùng hàm trong ConfigManager để trích xuất tên ảnh gốc từ nội dung JSON
                        json_display_name = self.config_manager.get_upload_display_name(data)

                        if json_display_name in pending_to_catch:
                            pending_to_catch.remove(json_display_name)
                            captured_responses.remove(data) # Xử lý xong thì xóa khỏi RAM luôn
                            self.write_flow_log("2.3", f"✅ Đã bắt được JSON của: {json_display_name}")

                    # Kiểm tra xem đã xong chưa
                    if not pending_to_catch:
                        self.write_flow_log("2.3", "🚀 Tuyệt vời! Đã bắt đủ toàn bộ JSON. Đi tiếp thôi.")
                        break
                    
                    # Quan trọng: Dùng wait_for_timeout của playwright để không treo luồng mạng
                    self.page.wait_for_timeout(2000) 
                else:
                    self.write_flow_log("2.3", f"⚠️ Hết 60s nhưng vẫn thiếu JSON của: {pending_to_catch}", "WARN")

            finally:
                self.page.remove_listener("response", handle_response)
                self.write_flow_log("2.3", "✅ Kết thúc quá trình.")

            time.sleep(1)
            self.action_click(self.locators["btn_config_main"], "3", "Mở Setting")
            self.page.get_by_role("tab", name="Video").click()
            if mode == "frames":
                self.page.get_by_role("tab", name="Khung hình").click()
                self.page.get_by_role("tab", name="9:16").click()
                self.page.get_by_role("tab", name="1x").click()
            else:
                self.page.get_by_role("tab", name="Thành phần").click()
            
            self.action_click("button[id^='radix-']:has-text('Veo 3.1')", "3.1.5", "Mở Model")
            self.action_click(f"div[role='menuitem']:has-text('Veo 3.1 - {model_type}')", "3.1.5", f"Chọn {model_type}")
            self.page.keyboard.press("Escape")

            if mode == "frames":
                for i, label in enumerate(["Bắt đầu", "Kết thúc"]):
                    if i >= len(img_list): break
                    
                    self.action_click(f"div[type='button']:has-text('{label}')", f"4.{i+1}", f"Mở danh sách {label}")
                    
                    img_name = os.path.basename(img_list[i])
                    self.write_flow_log(f"4.{i+1}", f"⌛ Server đang load ảnh... Tôi sẽ đợi đến khi thấy '{img_name}' mới thôi.")
                    
                    target_img = self.page.locator(f"div[role='option']:has-text('{img_name}')").last
                    
                    try:
                        target_img.wait_for(state="visible", timeout=0)
                        
                        target_img.click(force=True)
                        time.sleep(1)

                        # Bước mới: Click xác nhận "Thêm vào câu lệnh" sau khi chọn ảnh
                        btn_confirm = self.page.locator(self.locators["btn_add_to_prompt"])
                        if btn_confirm.is_visible(timeout=3000):
                            btn_confirm.click(force=True)
                            self.write_flow_log(f"4.{i+1}", "✅ Đã bấm 'Thêm vào câu lệnh'", "OK")

                        self.write_flow_log(f"4.{i+1}", f"✅ Hoàn tất chọn ảnh: {img_name}", "OK")
                        time.sleep(1)
                    except Exception as e:
                        self.write_flow_log(f"4.{i+1}", f"❌ Lỗi không mong muốn khi đợi ảnh: {e}", "FAIL")
                        return "FAIL_IMAGE_SELECT"
            
            editor = self.page.locator("div[data-slate-editor='true']").first
            editor.click()
            self.page.keyboard.press("Control+A")
            self.page.keyboard.press("Backspace")
            self.page.keyboard.type(prompt_text)

            self.action_click("button:has(i:text-is('arrow_forward'))", "6", "🚀 BẤM TẠO")
            return self.monitor_render_progress_and_download(save_dir, sku, profile_name, batch_id)

        except Exception as e:
            self.write_flow_log("ERROR", f"Lỗi thực thi: {e}", "FAIL")
            return "SYSTEM_ERROR"

    def monitor_render_progress_and_download(self, save_dir, sku, profile_name, batch_id):
        self.write_flow_log("WAIT", "⏳ AI đang Render: Đang theo dõi tiến độ...")
        start_time = time.time()
        last_percent = -1
        percent_visible_last_round = False 

        while time.time() - start_time < 1200:
            is_currently_progressing = False
            try:
                progress_loc = self.page.locator(self.locators["rendering_percentage"])
                if progress_loc.count() > 0 and progress_loc.last.is_visible(timeout=500):
                    percent_text = progress_loc.last.inner_text().strip()
                    current_percent = int(re.search(r'\d+', percent_text).group())
                    if current_percent > last_percent:
                        self.write_flow_log("PROGRESS", f"📊 Tiến độ: {percent_text}")
                        last_percent = current_percent
                    is_currently_progressing = True
                    percent_visible_last_round = True
            except: pass

            # 1. KIỂM TRA HOÀN THÀNH (SUCCESS)
            if not is_currently_progressing:
                if percent_visible_last_round:
                    time.sleep(2) 
                    percent_visible_last_round = False

                thumb = self.page.locator(self.locators["first_video_thumb"]).first
                if thumb.is_visible(timeout=2000):
                    self.write_flow_log("RENDER", "✅ ĐÃ THẤY VIDEO!", "OK")
                    thumb.click(force=True)
                    time.sleep(5)
                    return self.process_download(save_dir, sku, profile_name, batch_id)

            # ========================================================
            # 🔄 2. BẬT CHẾ ĐỘ TỰ CỨU (AUTO RETRY/REFRESH) KHI GẶP LỖI
            # ========================================================
            try:
                # Quét xem có thẻ thông báo lỗi truy cập cao hoặc xảy ra lỗi không
                error_loc = self.page.locator("//div[contains(., 'Rất tiếc, đã xảy ra lỗi') or contains(., 'lượng truy cập cao') or contains(., 'Không thành công')]").first
                
                if error_loc.is_visible(timeout=500):
                    self.write_flow_log("RENDER", "⚠️ Phát hiện lỗi hệ thống/quá tải! Chuẩn bị tự động cứu...", "WARN")
                    
                    # Chờ ngẫu nhiên từ 25 đến 30 giây
                    import random
                    wait_sec = random.uniform(25, 30)
                    self.write_flow_log("RENDER", f"⏳ Đang nghỉ {wait_sec:.1f}s để server ổn định trước khi thử nạp lại...")
                    time.sleep(wait_sec)
                    
                    # DANH SÁCH SELECTOR DỰ PHÒNG AN TOÀN (KHÔNG TRỘN LẪN CÚ PHÁP)
                    fallback_refresh_selectors = [
                        "button:has-text('Thử lại')",
                        "button:has-text('Retry')",
                        "button:has(i:text-is('refresh'))",
                        "//button[.//i[text()='refresh']]"
                    ]
                    
                    refresh_btn = None
                    for selector in fallback_refresh_selectors:
                        try:
                            loc = self.page.locator(selector).first
                            if loc.is_visible(timeout=500):
                                refresh_btn = loc
                                break
                        except:
                            continue
                    
                    if refresh_btn:
                        refresh_btn.click(force=True)
                        self.write_flow_log("RENDER", "🔄 Đã bấm nút REFRESH thành công! Khởi động lại thời gian chờ.", "OK")
                        
                        # Khởi động lại thời gian chờ
                        start_time = time.time()
                        last_percent = -1
                        time.sleep(5)
                        continue
                    else:
                        self.write_flow_log("RENDER", "❌ Không tìm thấy nút Refresh trên thẻ lỗi!", "FAIL")
            except Exception as e:
                self.write_flow_log("RENDER", f"⚠️ Lỗi phát sinh trong luồng cứu: {e}", "WARN")

            time.sleep(4) 
            
        return "TIMEOUT"

    def process_download(self, save_dir, sku, profile_name, batch_id):
        try:
            self.write_flow_log("6.2", "🚀 Bắt đầu tải video...")
            with self.page.expect_download(timeout=240000) as d_info:
                self.action_click(self.locators["btn_download_trigger"], "6.2", "Bấm nút Tải xuống")
            
            date_str = datetime.datetime.now().strftime('%Y-%m-%d')
            final_dir = os.path.join(save_dir, "videos", date_str, batch_id if batch_id else "Single")
            os.makedirs(final_dir, exist_ok=True)
            save_path = os.path.join(final_dir, f"{sku}.mp4")
            d_info.value.save_as(save_path)
            self.write_flow_log("DONE", f"💾 FILE ĐÃ LƯU: {sku}.mp4", "OK")
            try: self.page.locator("button:has-text('Xong'), button:has-text('Done')").click(timeout=3000)
            except: self.page.keyboard.press("Escape")
            return save_path
        except Exception as e:
            self.write_flow_log("DOWNLOAD", f"Lỗi tải file: {e}", "FAIL")
            return "DOWNLOAD_ERROR"