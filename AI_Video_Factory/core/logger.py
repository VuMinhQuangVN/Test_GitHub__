"""
Module logging dung chung cho toan bo project.

Thay vi dung print() rai rac (khong luu lai duoc, khong biet muc do
nghiem trong, khong co timestamp), moi noi trong code nen dung:

    from core.logger import get_logger
    log = get_logger(__name__)

    log.info("Da tao thu muc: %s", folder)
    log.warning("Khong xoa duoc file tam: %s", path)
    log.error("Crash khi render shot: %s", e, exc_info=True)

Log se vua in ra console (nhu print cu) vua ghi vao file
logs/app.log de xem lai sau khi bot da dong, huu ich khi debug
loi automation trinh duyet (VD: OUT_OF_CREDIT, RENDER_FAIL...).
"""
import logging
import os

_LOG_DIR = "logs"
_LOG_FILE = os.path.join(_LOG_DIR, "app.log")
_configured = False


def _configure_root_logger():
    global _configured
    if _configured:
        return
    os.makedirs(_LOG_DIR, exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Tra ve 1 logger da cau hinh san, dung __name__ cua module goi ham nay."""
    _configure_root_logger()
    return logging.getLogger(name)
