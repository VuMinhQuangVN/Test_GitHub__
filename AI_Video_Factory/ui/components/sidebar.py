from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QSpacerItem, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt
import qtawesome as qta

class Sidebar(QWidget):
    nav_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("Sidebar")
        self.buttons = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 10)
        layout.setSpacing(0)

        # Logo
        logo = QLabel("VEO3 ULTRA")
        logo.setObjectName("LogoLabel")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)

        # Menu Items
        menu_items = [
            ("Text to Video", "fa5s.file-video", "txt_vid"),
            ("Frames to Video", "fa5s.images", "frame_vid"),
            ("Nano Banana Pro", "fa5s.magic", "banana_pro"),
            ("Prompt Manager", "fa5s.edit", "prompt_mgr"), # <--- THÊM DÒNG NÀY
            ("Text to Audio", "fa5s.microphone", "txt_audio"),
            ("Video Merger", "fa5s.layer-group", "merger")
        ]

        for text, icon_str, nav_id in menu_items:
            btn = QPushButton(f"  {text}")
            btn.setObjectName("SidebarBtn")
            btn.setIcon(qta.icon(icon_str, color='#a0a5b8'))
            btn.setProperty("nav_id", nav_id)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(self.handle_click)
            layout.addWidget(btn)
            self.buttons.append(btn)

        # Spacer đẩy mọi thứ lên trên
        layout.addStretch(1)

        # Nút Settings ở dưới cùng (Fix lỗi attribute ở đây)
        self.settings_btn = QPushButton("  Settings") # Thêm self. vào đây
        self.settings_btn.setObjectName("SidebarBtn")
        self.settings_btn.setIcon(qta.icon('fa5s.cog', color='#a0a5b8'))
        layout.addWidget(self.settings_btn)

    def handle_click(self):
        btn = self.sender()
        nav_id = btn.property("nav_id")
        self.set_active_button(btn)
        self.nav_changed.emit(nav_id)

    def set_active_button(self, target_btn):
        # 1. Danh sách tất cả nút bao gồm cả nút Settings
        all_btns = self.buttons + [self.settings_btn]
        
        for btn in all_btns:
            # Tắt trạng thái active cũ
            btn.setProperty("active", "false")
            # Ép giao diện vẽ lại theo CSS (QSS)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
        # 2. Bật trạng thái active cho nút vừa bấm
        target_btn.setProperty("active", "true")
        target_btn.style().unpolish(target_btn)
        target_btn.style().polish(target_btn)