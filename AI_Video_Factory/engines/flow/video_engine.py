# import os
# from playwright.sync_api import sync_playwright
# from core.browser_manager import BrowserManager
# from pages.flow_page import FlowPage

# class VideoEngine:
#     def __init__(self, app_instance):
#         self.app = app_instance

#     def run(self, sku, image_base_path, video_scripts, start_profile, model_type):
#         """
#         Quy trình: Lấy list Nick -> Chạy Video -> Nếu hết lượt thì đổi Nick
#         video_scripts: List kịch bản từ Gemini/ChatGPT [{"prompt": "..."}, ...]
#         """
#         sku_folder = os.path.join(self.app.mgr.base_path, sku)
        
#         # 1. Thiết lập danh sách tài khoản xoay vòng
#         all_profiles = self.app.mgr.get_all_profiles()
        
#         # Tùy chọn: Nếu không ưu tiên PRO thì xóa PRO khỏi danh sách làm video
#         if not self.app.priority_pro_video and "chrome_auto_profile" in all_profiles:
#             all_profiles.remove("chrome_auto_profile")

#         # Xoay danh sách để bắt đầu từ Nick được chọn trên UI
#         if start_profile in all_profiles:
#             idx = all_profiles.index(start_profile)
#             all_profiles = all_profiles[idx:] + all_profiles[:idx]

#         profile_index = 0
        
#         # 2. Vòng lặp duyệt qua từng Take video (V1, V2...)
#         for i, script in enumerate(video_scripts):
#             take_id = f"{sku}_T{i+1}"
#             task_done = False
#             current_prompt = script['prompt']

#             # 3. Vòng lặp xoay Nick cho đến khi hoàn thành Task hiện tại
#             while not task_done and profile_index < len(all_profiles):
#                 profile = all_profiles[profile_index]
                
#                 # Check sổ đen (Blacklist)
#                 if not self.app.mgr.is_account_usable(profile):
#                     profile_index += 1
#                     continue

#                 self.app.write_log(f"🎬 [VIDEO-ENGINE] Take {i+1} đang dùng Nick: {profile}")

#                 try:
#                     with sync_playwright() as p:
#                         mgr = BrowserManager(profile_name=profile)
#                         context = mgr.init_browser(p)
#                         page = context.pages[0]
                        
#                         bot = FlowPage(page)
#                         bot.navigate()

#                         # Thực hiện tạo video
#                         res = bot.create_video(
#                             image_path=image_base_path,
#                             prompt_text=current_prompt,
#                             save_dir=sku_folder,
#                             profile_name=profile,
#                             sku=take_id,
#                             model_type=model_type
#                         )

#                         # Xử lý kết quả trả về từ Page
#                         if res == "LOW_CREDITS":
#                             self.app.write_log(f"🛑 Nick {profile} hết lượt. Đổi nick...")
#                             self.app.mgr.mark_account_empty(profile)
#                             context.close()
#                             mgr.cleanup_profile()
#                             profile_index += 1
#                             continue # Quay lại loop 'while' thử nick mới
                        
#                         if res == "STUCK_AT_99":
#                             self.app.write_log(f"⚠️ Kẹt 99% tại {profile}. Dừng để kiểm tra.")
#                             context.close()
#                             mgr.cleanup_profile()
#                             return False # Dừng toàn bộ Engine

#                         if res == "RENDER_FAILED":
#                             self.app.write_log("⚠️ Render lỗi (Prompt). Nhờ AI sửa kịch bản...")
                            
#                             # Gọi hàm ChatGPT từ UI để nhờ sửa lỗi
#                             # Lưu ý: fixed_data là kết quả trả về từ ChatGPT
#                             fixed_data = self.app.ask_chatgpt_for_script(
#                                 image_base_path, 
#                                 style, 
#                                 en_prod, 
#                                 is_retry=True, 
#                                 failed_prompt=current_prompt
#                             )
                            
#                             if fixed_data:
#                                 # Giải thích: ChatGPT có thể trả về 1 List [{},{}] hoặc 1 Dict {}
#                                 # Dòng này đảm bảo bốc được chuỗi 'prompt' ra dù kết quả là kiểu gì
#                                 if isinstance(fixed_data, list):
#                                     current_prompt = fixed_data[0]['prompt']
#                                 else:
#                                     current_prompt = fixed_data['prompt']
                                    
#                                 self.app.write_log(f"📝 Prompt mới: {current_prompt[:50]}...")
#                                 context.close()
#                                 mgr.cleanup_profile()
#                                 continue # Quay lại đầu vòng lặp while để thử lại với nick này
#                             else:
#                                 self.app.write_log("❌ ChatGPT không sửa được. Đổi nick...")
#                                 profile_index += 1
#                                 break

#                         if res and res not in ["RENDER_FAILED", "TIMEOUT", "SYSTEM_ERROR"]:
#                             self.app.write_log(f"✅ Take {i+1} hoàn thành!")
#                             task_done = True
#                             context.close()
#                             mgr.cleanup_profile()

#                 except Exception as e:
#                     self.app.write_log(f"❌ Lỗi Engine tại {profile}: {e}")
#                     profile_index += 1

#         self.app.write_log("🎉 [VIDEO-ENGINE] Đã sản xuất xong tất cả các Take.")
#         return True