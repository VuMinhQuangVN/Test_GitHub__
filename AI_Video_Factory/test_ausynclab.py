# -*- coding: utf-8 -*-
import sys
import os
import time
import json
import urllib.request
import urllib.error
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QComboBox, QTextEdit, QDoubleSpinBox, QMessageBox, QGroupBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from core.config_manager import ConfigManager
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# =======================================================
# THỢ NGẦM 1: LẤY DANH SÁCH GIỌNG NÓI CLONE (GET)
# =======================================================
class FetchVoicesWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, api_key):
        super().__init__()
        self.api_key = api_key

    def run(self):
        url = "https://api.ausynclab.io/api/v1/voices/list"
        req = urllib.request.Request(url)
        req.add_header("accept", "application/json")
        req.add_header("X-API-Key", self.api_key)
        req.add_header("User-Agent", USER_AGENT)
        
        try:
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                voices = res_data.get("result", [])
                self.finished.emit(voices)
        except urllib.error.HTTPError as e:
            self.error.emit(f"HTTP Error {e.code}: {e.reason}")
        except Exception as e:
            self.error.emit(str(e))

# =======================================================
# THỢ NGẦM 2: SINH GIỌNG NÓI & THĂM DÒ TRẠNG THÁI (POST & POLL)
# =======================================================
class GenerateTTSWorker(QThread):
    log_signal = pyqtSignal(str, str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, api_key, payload):
        super().__init__()
        self.api_key = api_key
        self.payload = payload

    def run(self):
        url_post = "https://api.ausynclab.io/api/v1/speech/text-to-speech"
        headers = {
            "accept": "application/json",
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT
        }
        
        self.log_signal.emit("📤 Đang gửi yêu cầu sinh giọng nói lên AusyncLab...", "INFO")
        
        try:
            data = json.dumps(self.payload).encode('utf-8')
            req = urllib.request.Request(url_post, data=data, headers=headers, method="POST")
            
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                audio_id = res_data.get("result", {}).get("audio_id")
                
            if not audio_id:
                self.error.emit("Thất bại: API không trả về audio_id!")
                return
                
            self.log_signal.emit(f"✅ Đã tạo tác vụ thành công! ID Audio: {audio_id}", "OK")
            
            # Thăm dò (Polling) liên tục mỗi 3s
            url_poll = f"https://api.ausynclab.io/api/v1/speech/{audio_id}"
            req_poll = urllib.request.Request(url_poll)
            req_poll.add_header("accept", "application/json")
            req_poll.add_header("X-API-Key", self.api_key)
            req_poll.add_header("User-Agent", USER_AGENT) # <--- SỬA LỖI 403 Ở ĐÂY!
            
            start_time = time.time()
            timeout_limit = 180 # Đợi tối đa 3 phút
            
            while time.time() - start_time < timeout_limit:
                time.sleep(3) 
                
                try:
                    with urllib.request.urlopen(req_poll) as response:
                        poll_data = json.loads(response.read().decode('utf-8'))
                        result = poll_data.get("result", {})
                        state = result.get("state", "PROCESSING")
                        audio_url = result.get("audio_url", "")
                        
                        # TỰ ĐỘNG DÒ KHÓA CHỨA THỨ TỰ HÀNG CHỜ TRONG KẾT QUẢ THÔ
                        queue_info = ""
                        for key in ["queue_position", "position", "waiting_count", "index", "waiting"]:
                            if key in result:
                                queue_info = f" | Hàng chờ số: {result[key]}"
                                break
                        
                        self.log_signal.emit(f"⚙️ Trạng thái: {state}{queue_info}", "INFO")
                        
                        if state == "SUCCEED" and audio_url:
                            self.log_signal.emit("🎉 AI đã chuyển đổi giọng nói thành công!", "OK")
                            self.finished.emit(audio_url)
                            return
                        elif state == "FAILED":
                            self.error.emit("AusyncLab báo cáo tác vụ sinh giọng nói bị THẤT BẠI.")
                            return
                except urllib.error.HTTPError as e:
                    self.log_signal.emit(f"⚠️ Trạng thái mạng: {e.code} {e.reason}", "WARN")
                except Exception as e:
                    self.log_signal.emit(f"⚠️ Đang kết nối: {e}", "WARN")
                    
            self.error.emit("Quá thời gian chờ (Timeout) 3 phút mà không nhận được file.")
            
        except urllib.error.HTTPError as e:
            self.error.emit(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
        except Exception as e:
            self.error.emit(str(e))

# =======================================================
# THỢ NGẦM 3: LẤY LỊCH SỬ ĐÃ TẠO (GET)
# =======================================================
class FetchHistoryWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, api_key):
        super().__init__()
        self.api_key = api_key

    def run(self):
        url = "https://api.ausynclab.io/api/v1/speech/"
        req = urllib.request.Request(url)
        req.add_header("accept", "application/json")
        req.add_header("X-API-Key", self.api_key)
        req.add_header("User-Agent", USER_AGENT)
        
        try:
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                history = res_data.get("result", [])
                self.finished.emit(history)
        except urllib.error.HTTPError as e:
            self.error.emit(f"HTTP Error {e.code}: {e.reason}")
        except Exception as e:
            self.error.emit(str(e))

# =======================================================
# GIAO DIỆN KIỂM THỬ CHÍNH (LAYOUT 2 CỘT)
# =======================================================
class AusyncLabTestApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VEO3 - BỘ THỬ NGHIỆM GIỌNG NÓI AUSYNCLAB API")
        self.resize(1200, 800)
        self.mgr = ConfigManager()
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout tổng chia 2 cột chính
        screen_layout = QHBoxLayout(central_widget)
        screen_layout.setSpacing(15)

        # ---------------------------------------------------------
        # CỘT TRÁI: ĐIỀU KHIỂN & CẤU HÌNH (CHIẾM 5 PHẦN)
        # ---------------------------------------------------------
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        # Style màu tối
        self.setStyleSheet("""
            QMainWindow { background-color: #0b0d14; }
            QLabel { color: #aaa; font-weight: bold; font-size: 13px; }
            QLineEdit, QComboBox, QTextEdit { 
                background-color: #161926; color: #eee; border: 1px solid #333; 
                border-radius: 6px; padding: 8px; font-size: 13px;
            }
            QPushButton {
                background-color: #4CAF50; color: white; font-weight: bold;
                font-size: 14px; border: none; border-radius: 6px; padding: 8px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)

        # Phần 1: Xác thực API
        auth_group = QGroupBox("🔑 Xác thực tài khoản")
        auth_layout = QHBoxLayout(auth_group)
        self.txt_api_key = QLineEdit()
        self.txt_api_key.setPlaceholderText("Dán X-API-Key AusyncLab...")
        self.txt_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.btn_fetch_voices = QPushButton("⭐ Quét Giọng Clone")
        self.btn_fetch_voices.setFixedWidth(150)
        self.btn_fetch_voices.clicked.connect(self.fetch_cloned_voices)
        
        auth_layout.addWidget(QLabel("API Key:"))
        auth_layout.addWidget(self.txt_api_key)
        auth_layout.addWidget(self.btn_fetch_voices)
        left_layout.addWidget(auth_group)

        # Phần 2: Cấu hình
        config_group = QGroupBox("🎙️ Cấu hình bộ chuyển đổi giọng nói")
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(8)
        
        row1 = QHBoxLayout()
        self.cb_voices = QComboBox()
        self.cb_voices.addItem("Chưa quét danh sách giọng nói...", "")
        row1.addWidget(QLabel("Giọng Clone:"))
        row1.addWidget(self.cb_voices, 1)
        
        row2 = QHBoxLayout()
        self.cb_model = QComboBox()
        self.cb_model.addItems(["myna-1-turbo", "myna-2", "myna-1"])
        self.cb_lang = QComboBox()
        self.cb_lang.addItems(["vi", "en"])
        self.spin_speed = QDoubleSpinBox()
        self.spin_speed.setRange(0.75, 1.25)
        self.spin_speed.setValue(1.00)
        self.spin_speed.setSingleStep(0.05)
        self.spin_speed.setStyleSheet("background: #161926; color: white;")
        
        row2.addWidget(QLabel("Model:"))
        row2.addWidget(self.cb_model)
        row2.addWidget(QLabel("Ngôn ngữ:"))
        row2.addWidget(self.cb_lang)
        row2.addWidget(QLabel("Tốc độ:"))
        row2.addWidget(self.spin_speed)
        
        config_layout.addLayout(row1)
        config_layout.addLayout(row2)
        left_layout.addWidget(config_group)

        # Phần 3: Nhập liệu
        left_layout.addWidget(QLabel("✍️ NHẬP VĂN BẢN CẦN CHUYỂN THÀNH GIỌNG NÓI:"))
        self.txt_input = QTextEdit()
        self.txt_input.setPlaceholderText("Nhập văn bản thoại...")
        self.txt_input.setText("Trời ơi cái áo này mặc lên nhìn gọn người ghê luôn á, chất vải cực kỳ mềm mại dã man.")
        self.txt_input.setMaximumHeight(150)
        left_layout.addWidget(self.txt_input)

        # Phần 4: Nút chạy
        self.btn_generate = QPushButton("🚀 CHẠY THỬ NGHIỆM CHUYỂN VĂN BẢN")
        self.btn_generate.setMinimumHeight(45)
        self.btn_generate.setStyleSheet("background-color: #9C27B0; color: white; font-weight: bold; font-size: 15px;")
        self.btn_generate.clicked.connect(self.generate_speech)
        left_layout.addWidget(self.btn_generate)

        screen_layout.addWidget(left_container, 5) # Cột trái chiếm 5 phần

        # ---------------------------------------------------------
        # CỘT PHẢI: LOGS & LỊCH SỬ ĐÃ TẠO (CHIẾM 5 PHẦN)
        # ---------------------------------------------------------
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        # Phần 5: Real-time Log
        right_layout.addWidget(QLabel("📋 TIẾN TRÌNH API LOG REAL-TIME:"))
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet("background-color: #0b0d14; color: #4CAF50; font-family: 'Consolas'; font-size: 12px;")
        right_layout.addWidget(self.txt_log, 4)

        # Phần 6: Lịch sử Audio đã tạo
        history_box = QGroupBox("📜 Lịch sử các Audio đã tạo")
        history_layout = QVBoxLayout(history_box)
        
        self.btn_fetch_history = QPushButton("🔄 Quét & Cập nhật Lịch Sử")
        self.btn_fetch_history.setStyleSheet("background-color: #00BCD4; color: white; font-weight: bold;")
        self.btn_fetch_history.clicked.connect(self.fetch_history)
        
        self.txt_history = QTextEdit()
        self.txt_history.setReadOnly(True)
        self.txt_history.setPlaceholderText("Bấm Quét Lịch Sử để hiển thị danh sách các audio cũ...")
        self.txt_history.setStyleSheet("background-color: #0c0e17; color: #abb2bf; font-family: 'Consolas'; font-size: 11px;")
        
        history_layout.addWidget(self.btn_fetch_history)
        history_layout.addWidget(self.txt_history)
        right_layout.addWidget(history_box, 6)

        screen_layout.addWidget(right_container, 5) # Cột phải chiếm 5 phần

    def log(self, message, status="INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        color = "#4CAF50"
        if status == "FAIL" or status == "ERROR": color = "red"
        elif status == "WARN": color = "orange"
        self.txt_log.append(f"<font color='gray'>[{ts}]</font> <font color='{color}'><b>[{status}]</b> {message}</font>")

    def fetch_cloned_voices(self):
        key = self.txt_api_key.text().strip()
        if not key:
            QMessageBox.warning(self, "Trống", "Vui lòng nhập X-API-Key trước!")
            return
            
        self.btn_fetch_voices.setEnabled(False)
        self.log("📡 Đang quét danh sách giọng nói Clone của bạn...")
        
        self.fetch_worker = FetchVoicesWorker(key)
        self.fetch_worker.finished.connect(self.on_voices_fetched)
        self.fetch_worker.error.connect(self.on_fetch_error)
        self.fetch_worker.start()

    def on_voices_fetched(self, voices):
        self.btn_fetch_voices.setEnabled(True)
        self.cb_voices.clear()
        
        if not voices:
            self.cb_voices.addItem("Thư viện giọng nói của bạn trống rỗng!", "")
            self.log("⚠️ Không tìm thấy giọng nói clone nào trong thư viện.", "WARN")
            return
            
        for v in voices:
            v_id = v.get("id")
            name = v.get("name", "Unnamed")
            lang = v.get("language", "vi")
            gender = v.get("gender", "FEMALE")
            self.cb_voices.addItem(f"ID: {v_id} | Tên: {name} ({gender} - {lang.upper()})", v_id)
            
        self.log(f"✅ Đã nạp thành công {len(voices)} giọng nói Clone vào danh sách!", "OK")
        
        # Tiện thể, tự động cập nhật luôn lịch sử
        self.fetch_history()

    def on_fetch_error(self, err_msg):
        self.btn_fetch_voices.setEnabled(True)
        self.log(f"❌ Không thể lấy danh sách giọng nói: {err_msg}", "FAIL")
        QMessageBox.critical(self, "Lỗi kết nối", f"Lỗi quét danh sách giọng nói:\n{err_msg}")

    def generate_speech(self):
        key = self.txt_api_key.text().strip()
        voice_id = self.cb_voices.currentData()
        text = self.txt_input.toPlainText().strip()
        
        if not key or not voice_id or not text:
            QMessageBox.warning(self, "Thiếu thông tin", "Hãy chắc chắn bạn đã: Điền API Key, Quét chọn Giọng nói, và Nhập Văn bản thoại!")
            return
            
        self.btn_generate.setEnabled(False)
        self.txt_log.clear()
        
        payload = {
            "audio_name": f"Test_VEO3_{int(time.time())}",
            "text": text,
            "voice_id": int(voice_id),
            "speed": float(self.spin_speed.value()),
            "model_name": self.cb_model.currentText(),
            "language": self.cb_lang.currentText(),
            "callback_url": "https://example.com/dummy-callback" 
        }
        
        self.tts_worker = GenerateTTSWorker(key, payload)
        self.tts_worker.log_signal.connect(self.log)
        self.tts_worker.finished.connect(self.on_tts_finished)
        self.tts_worker.error.connect(self.on_tts_error)
        self.tts_worker.start()

    def on_tts_finished(self, audio_url):
        self.btn_generate.setEnabled(True)
        self.log(f"💾 ĐÃ SINH XONG FILE GHI ÂM!", "OK")
        self.log(f"🔗 Link tải file: {audio_url}", "OK")
        
        # Cập nhật lịch sử tự động sau khi sinh xong file mới
        self.fetch_history()
        
        reply = QMessageBox.question(self, "Tạo thành công", f"Đã sinh xong file ghi âm!\nBạn có muốn mở link để tải file về không?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            import webbrowser
            webbrowser.open(audio_url)

    def on_tts_error(self, err_msg):
        self.btn_generate.setEnabled(True)
        self.log(f"❌ Lỗi sinh giọng nói: {err_msg}", "FAIL")
        QMessageBox.critical(self, "Thất bại", f"Quá trình chuyển đổi bị lỗi:\n{err_msg}")

    # =======================================================
    # LOGIC MỚI: QUÉT & CẬP NHẬT LỊCH SỬ AUDIO
    # =======================================================
    def fetch_history(self):
        key = self.txt_api_key.text().strip()
        if not key: return
        
        self.btn_fetch_history.setEnabled(False)
        self.history_worker = FetchHistoryWorker(key)
        self.history_worker.finished.connect(self.on_history_fetched)
        self.history_worker.error.connect(self.on_history_error)
        self.history_worker.start()

    def on_history_fetched(self, history):
        self.btn_fetch_history.setEnabled(True)
        self.txt_history.clear()
        
        if not history:
            self.txt_history.append("Lịch sử tạo audio của bạn trống rỗng.")
            return
            
        self.txt_history.append(f"📋 TỔNG SỐ FILE ĐÃ TẠO: {len(history)}\n" + "=" * 50)
        
        for item in history[:15]: # Chỉ hiển thị 15 file gần đây nhất cho đỡ rối mắt
            h_id = item.get("id")
            name = item.get("name", "Unnamed")
            state = item.get("state", "UNKNOWN")
            url = item.get("audio_url", "No URL")
            voice_name = item.get("voice_name", "Giọng ẩn")
            created_at = item.get("created_at", "")
            
            # Cắt ngắn thời gian cho dễ nhìn
            if created_at: created_at = created_at.replace("T", " ")[:19]
            
            status_emoji = "✅" if state == "SUCCEED" else "⏳" if state == "PROCESSING" else "❌"
            
            self.txt_history.append(
                f"{status_emoji} [ID: {h_id}] {name}\n"
                f"   🎙️ Giọng: {voice_name} | Lúc: {created_at}\n"
                f"   🔗 Link: {url}\n"
                f"--------------------------------------------------"
            )

    def on_history_error(self, err_msg):
        self.btn_fetch_history.setEnabled(True)
        print(f"❌ Lỗi lấy lịch sử: {err_msg}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AusyncLabTestApp()
    window.show()
    sys.exit(app.exec())