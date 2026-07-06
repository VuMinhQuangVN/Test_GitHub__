import sys, os, time
from playwright.sync_api import sync_playwright
from core.browser_manager import BrowserManager
from bots.chatgpt_images_page import ChatGPTImagesPage

def run_debug_upload():
    profile_name = "google_acc_1" 
    
    test_images = [
        r"F:\Data_Tool\Ao_Hoodee_01\base_Ao_Hoodee_01_close_angle_A.jpg",
        r"F:\Data_Tool\Ao_Hoodee_01\base_Ao_Hoodee_01_close_angle_B.jpg",
        r"F:\Data_Tool\Ao_Hoodee_01\base_Ao_Hoodee_01_medium_shot_A.jpg"
    ]

    print(f"🚀 [DEBUG] Đang khởi động trình duyệt cho: {profile_name}")

    with sync_playwright() as p:
        bm = BrowserManager(profile_name=profile_name)
        context = bm.init_browser(p, headless=False, slow_mo=300)
        page = context.pages[0]
        bot = ChatGPTImagesPage(page)
        
        print("🌐 Đang vào ChatGPT...")
        bot.navigate()
        time.sleep(5)

        print("📤 Thực hiện nạp 3 ảnh để kích hoạt lỗi...")
        try:
            # Click nút Plus
            page.locator(bot.locators["btn_plus"]).click(force=True)
            time.sleep(1)
            
            # Kích hoạt File Chooser
            with page.expect_file_chooser() as fc_info:
                page.locator(bot.locators["menu_item_upload"]).first.click(force=True)
            
            # Nạp ảnh
            fc_info.value.set_files(test_images)
            print("⏳ Đã gửi lệnh nạp file, đang quét thông báo lỗi...")

            # --- ĐOẠN QUÉT PHÁT HIỆN LỖI ---
            found_error = False
            error_text = "You may only upload 1 files at a time"
            
            # Quét trong vòng 5 giây để đợi thông báo hiện ra
            for i in range(10): 
                # Tìm tất cả các element chứa đoạn text lỗi
                # exact=False để nó bắt được cả khi text nằm trong các chuỗi dài hơn
                error_locator = page.get_by_text(error_text, exact=False)
                
                if error_locator.count() > 0 and error_locator.first.is_visible():
                    print("\n" + "!"*40)
                    print(f"🚨 [DETECTED] ĐÃ PHÁT HIỆN LỖI: '{error_text}'")
                    print("!"*40 + "\n")
                    
                    # Khoanh vùng cái thông báo lỗi đó bằng màu vàng để bạn nhìn thấy trên màn hình
                    error_locator.first.evaluate("el => el.style.outline = '5px solid yellow'")
                    found_error = True
                    break
                time.sleep(0.5)

            if not found_error:
                print("✅ Không tìm thấy thông báo lỗi (Có thể nick này chưa bị giới hạn).")

            # Dừng lại để bạn xem kết quả trên trình duyệt trước khi đóng
            print("👉 Đã dừng lại (Pause). Nhấn Resume trên Inspector hoặc đóng terminal để kết thúc.")
            page.pause()

        except Exception as e:
            print(f"❌ Lỗi debug: {e}")
            page.pause()

        context.close()

if __name__ == "__main__":
    sys.path.append(os.getcwd())
    run_debug_upload()