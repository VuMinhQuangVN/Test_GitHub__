# debug_selector.py
from playwright.sync_api import sync_playwright
from core.browser_manager import BrowserManager
import time

def run_debug():
    # 1. Chọn nick bạn muốn soi (Ví dụ nick 6)
    profile_to_check = "chrome_auto_profile" 
    
    print(f"🚀 Đang mở trình duyệt soi mã cho: {profile_to_check}")
    
    with sync_playwright() as p:
        bm = BrowserManager(profile_name=profile_to_check)
        
        # 2. Mở trình duyệt (Hiện hình, có SlowMo để dễ nhìn)
        # Chúng ta dùng hàm init_browser bạn vừa cập nhật
        context = bm.init_browser(p, headless=False, slow_mo=500)
        
        page = context.pages[0]
        
        # 3. Truy cập trang web
        page.goto("https://labs.google/fx/vi/tools/flow")
        
        print("\n=== CHẾ ĐỘ SOI MÃ ĐANG BẬT ===")
        print("1. Cửa sổ 'Playwright Inspector' sẽ hiện ra.")
        print("2. Bạn bấm vào nút 'Thành phần' trên web.")
        print("3. Nhìn vào Inspector để lấy Selector (Mã nút).")
        print("4. Sau khi xong, hãy đóng trình duyệt để kết thúc.")
        
        # ĐÂY LÀ CÂU LỆNH THẦN THÁNH ĐỂ BẬT CODEGEN TRONG CODE
        page.pause() 
        
        context.close()

if __name__ == "__main__":
    run_debug()