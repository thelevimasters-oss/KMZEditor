import os, sys
from PySide6 import QtCore, QtGui, QtWidgets

APP_NAME = "KMZ Studio"

def main():
    os.environ.setdefault("QT_OPENGL", "software")
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu --disable-gpu-compositing")
    os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")
    os.environ.setdefault("KMZ_NO_WEBENGINE", "1")

    def _excepthook(etype, e, tb):
        import traceback
        msg = "".join(traceback.format_exception(etype, e, tb))
        try:
            QtWidgets.QMessageBox.critical(None, "KMZ Studio crashed", msg)
        except Exception:
            pass
        print(msg, flush=True)
    sys.excepthook = _excepthook

    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    from .ui.main_window import MainWindow
    from .core.utils import init_logging, get_app_data_dir

    log_dir = get_app_data_dir()
    os.makedirs(log_dir, exist_ok=True)
    init_logging(os.path.join(log_dir, "kmz_studio.log"))

    f = app.font()
    if f.pointSize() < 11:
        f.setPointSize(11)
        app.setFont(f)

    mw = MainWindow()
    mw.show()
    sys.exit(app.exec())
