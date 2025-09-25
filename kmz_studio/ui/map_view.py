import os, tempfile
from pathlib import Path
from PySide6 import QtCore, QtWidgets, QtGui

QtWebEngineWidgets = None  # hard-disable embedded map
os.environ["KMZ_NO_WEBENGINE"] = "1"

class MapView(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tmp = tempfile.TemporaryDirectory(prefix="kmzstudio_map_")
        self._html_path = Path(self._tmp.name) / "map.html"
        lay = QtWidgets.QVBoxLayout(self); lay.setContentsMargins(0,0,0,0)
        box = QtWidgets.QGroupBox("Map preview (opened in your browser)")
        v = QtWidgets.QVBoxLayout(box)
        msg = QtWidgets.QLabel("Click the button to open the current map in your default browser.")
        btn = QtWidgets.QPushButton("Open Map in Browser")
        btn.clicked.connect(self._open_in_browser)
        v.addWidget(msg); v.addWidget(btn); v.addStretch(1)
        lay.addWidget(box)

    def _open_in_browser(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(self._html_path)))

    def set_html(self, html: str):
        self._html_path.write_text(html, encoding="utf-8")
