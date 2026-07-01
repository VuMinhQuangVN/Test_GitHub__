import os
import time
from playwright.sync_api import sync_playwright
from core.browser_manager import BrowserManager

def run_setup():
    print("======================================================")
    print(" 🛠️  TOOL KHỞI TẠO & ĐĂNG NHẬP ĐA TÀI KHOẢN GOOGLE 🛠️")
    print("======================================================")
    
    # Bước 1: Hỏi ID tài khoản để đặt tên thư mục profile
    acc_id = input("👉 Nhập số thứ tự tài khoản (Ví dụ: 1, 2, 3... hoặc để trống cho nick chính): ").strip()
    
    if not acc_id:
        profile_name = "chrome_auto_profile" # Nick chính cũ của bạn
    else:
        profile_name = f"google_acc_{acc_id}" # Các nick phụ 1, 2, 3...
        
    print(f"🚀 Đang khởi tạo trình duyệt cho Profile: {profile_name}")
    
    with sync_playwright() as p:
        # 2. Gọi BrowserManager với tên profile cụ thể
        manager = BrowserManager(profile_name=profile_name)
        context = manager.init_browser(p)
        page = context.pages[0]
        
        # 3. Mở cả Gemini và Flow để check đăng nhập
        print(f"🌐 Đang mở Gemini & Flow...")
        page.goto("https://gemini.google.com/app")
        
        # Mở thêm tab Flow để bạn đăng nhập một thể (Google dùng chung session)
        # page.context.new_page().goto("https://labs.google/fx/vi/tools/flow")

        print("\n👉 HƯỚNG DẪN THAO TÁC TAY:")
        print(f"--- ĐANG THIẾT LẬP CHO: {profile_name} ---")
        print("1. Đăng nhập tài khoản Google vào cửa sổ Chrome vừa hiện ra.")
        print("2. Chấp nhận các điều khoản của Gemini và Google Labs Flow.")
        print("3. Khi đã vào được giao diện sử dụng, hãy bấm nút [X] đóng Chrome để LƯU.")
        
        print("\n⏳ Tool đang chờ bạn thao tác... Đừng vội tắt Terminal này nhé!")
        
        try:
            # Giữ trình duyệt mở cho đến khi bạn tự tay đóng nó
            page.wait_for_event("close", timeout=0) 
        except Exception:
            pass 

        time.sleep(1000)  # Đợi chút để đảm bảo dữ liệu đã được lưu
        print(f"\n✅ Đã lưu xong dữ liệu đăng nhập vào thư mục: '{profile_name}'")
        print(f"🎉 Bây giờ bạn có thể dùng Profile này trong Tool Automation!")

if __name__ == "__main__":
    run_setup()