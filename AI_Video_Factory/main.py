import sys
import os

# Luon dat thu muc lam viec la thu muc chua file main.py nay,
# bat ke ban dang dung o dau khi go lenh chay python.
# Neu khong lam vay, cac thu muc database/profiles/logs se bi tao nham
# ra ben ngoai AI_Video_Factory (vi du ra thu muc cha Test_GitHub).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Import Core và UI
from core.config_manager import ConfigManager
from ui.main_window import MainWindow
from core.logger import get_logger

log = get_logger(__name__)

def setup_environment():
    """Khởi tạo môi trường làm việc cơ bản"""
    # Đảm bảo các thư mục cần thiết tồn tại
    folders = ["database", "profiles", "logs"]
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            log.info("Da tao thu muc: %s", folder)

def main():
    # 1. Tối ưu hiển thị cho màn hình 4K/High-DPI
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    # 2. Khởi tạo ứng dụng Qt
    app = QApplication(sys.argv)
    app.setStyle("Fusion") # Dùng style Fusion để giao diện đồng nhất trên Win/Mac
    
    # 3. Thiết lập môi trường và cấu hình
    setup_environment()
    
    # Giả sử ổ lưu trữ mặc định của bạn là ổ F hoặc thư mục hiện tại
    # Bạn có thể thay đổi đường dẫn này tùy theo máy
    base_storage = "F:/Data_Tool" if os.path.exists("F:/") else os.path.join(os.getcwd(), "output")
    
    try:
        # Khởi tạo ConfigManager (Dependency Injection vào MainWindow)
        config_mgr = ConfigManager(base_storage)
        
        # 4. Khởi tạo Giao diện chính
        window = MainWindow(config_manager=config_mgr)
        window.show()
        
        log.info("He thong VEO3 ULTRA da san sang!")
        
        # 5. Chạy vòng lặp sự kiện
        sys.exit(app.exec())
        
    except Exception as e:
        log.error("Loi khoi dong he thong: %s", e, exc_info=True)
        input("Nhấn Enter để thoát...")

if __name__ == "__main__":
    main()

