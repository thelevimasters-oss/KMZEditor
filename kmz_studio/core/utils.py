import os, sys, logging
from logging.handlers import RotatingFileHandler
from PySide6 import QtWidgets, QtCore

def get_logger():
    logger = logging.getLogger("kmz_studio")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
    return logger

def init_logging(log_path: str):
    logger = get_logger()
    if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
        handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        handler.setFormatter(fmt)
        logger.addHandler(handler)
        logger.info("Logging to %s", log_path)

def install_qt_console_handler(emitter_obj):
    class QtConsoleHandler(logging.Handler):
        def emit(self, record):
            msg = self.format(record)
            try:
                emitter_obj.emit(msg)
            except Exception:
                pass
    logger = get_logger()
    handler = QtConsoleHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(handler)

def get_app_data_dir() -> str:
    if sys.platform.startswith("win"):
        base = os.getenv("APPDATA", os.path.expanduser("~"))
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.getenv("XDG_STATE_HOME", os.path.expanduser("~/.local/state"))
    return os.path.join(base, "kmz_studio")

class NonBlockingProgress(QtWidgets.QProgressDialog):
    def __init__(self, parent, title, label, determinate: bool=False):
        super().__init__(label, "Cancel", 0, 0, parent)
        self.setWindowTitle(title)
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setAutoClose(False); self.setAutoReset(False)
        self._cancelled = False
        self.canceled.connect(lambda: setattr(self, "_cancelled", True))
        self.setMinimumDuration(300)
    def set_range(self, a, b): self.setRange(a, b)
    def is_cancelled(self): return self._cancelled
    def __enter__(self): self.show(); QtWidgets.QApplication.processEvents(); return self
    def __exit__(self, exc_type, exc, tb): self.reset(); self.close()
def info_message(parent, title, text): QtWidgets.QMessageBox.information(parent, title, text)
def warn_message(parent, title, text): QtWidgets.QMessageBox.warning(parent, title, text)
def error_message(parent, title, text): QtWidgets.QMessageBox.critical(parent, title, text)
