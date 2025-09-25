import os
from pathlib import Path
from PySide6 import QtCore, QtGui, QtWidgets
from .tree_panel import KMLTreePanel
from .properties_panel import PropertiesPanel
from .map_view import MapView
from .dialogs import confirm_overwrite, save_file_dialog, open_kmz_dialog, export_selected_dialog
from ..core import kmz_io, exporters, map_renderer
from ..core.utils import get_logger, NonBlockingProgress, info_message, warn_message, error_message
from ..core.edit import NameEditCommand
from ..core.kml_model import KMLDocument

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("KMZ Studio")
        self.resize(1320, 840)

        self.logger = get_logger()
        self.current_doc: KMLDocument | None = None
        self.current_kmz_path: str | None = None
        self.undo_stack = QtGui.QUndoStack(self)

        self.splitter = QtWidgets.QSplitter(self)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.setCentralWidget(self.splitter)

        self.tree_panel = KMLTreePanel(self)
        self.tree_panel.setMinimumWidth(280)
        self.tree_panel.nodeSelectionChanged.connect(self._on_node_selected)
        self.tree_panel.visibilityChanged.connect(self._on_visibility_changed)
        self.tree_panel.requestRefreshMap.connect(self._refresh_map)

        self.map_view = MapView(self)
        self.props_panel = PropertiesPanel(self)
        self.props_panel.applyRequested.connect(self._apply_properties)

        self.log_console = QtWidgets.QPlainTextEdit(self)
        self.log_console.setReadOnly(True)
        self.log_console.setMaximumHeight(180)
        self.log_console.setPlaceholderText("Log output...")
        self.log_dock = QtWidgets.QDockWidget("Console / Log", self)
        self.log_dock.setObjectName("LogDock")
        self.log_dock.setWidget(self.log_console)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.log_dock)

        self.splitter.addWidget(self.tree_panel)
        self.splitter.addWidget(self.map_view)
        self.splitter.addWidget(self.props_panel)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 2)
        self.splitter.setStretchFactor(2, 0)

        self._make_actions()
        self._make_menus_and_toolbar()
        self._apply_default_styles()
        self._install_log_handler()

    def _make_actions(self):
        self.act_open = QtGui.QAction("Open KMZ…", self)
        self.act_open.setShortcut(QtGui.QKeySequence.Open)
        self.act_open.triggered.connect(self._open_kmz)

        self.act_save = QtGui.QAction("Save", self)
        self.act_save.setShortcut(QtGui.QKeySequence.Save)
        self.act_save.triggered.connect(self._save_kmz)

        self.act_save_as = QtGui.QAction("Save As…", self)
        self.act_save_as.setShortcut(QtGui.QKeySequence("Ctrl+Shift+S"))
        self.act_save_as.triggered.connect(lambda: self._save_kmz(save_as=True))

        self.act_export = QtGui.QAction("Export…", self)
        self.act_export.setShortcut(QtGui.QKeySequence("Ctrl+E"))
        self.act_export.triggered.connect(self._export_selected)

        self.act_undo = self.undo_stack.createUndoAction(self, "Undo")
        self.act_undo.setShortcut(QtGui.QKeySequence.Undo)
        self.act_redo = self.undo_stack.createRedoAction(self, "Redo")
        self.act_redo.setShortcut(QtGui.QKeySequence.Redo)

        self.act_theme = QtGui.QAction("High Contrast Theme", self, checkable=True, checked=False)
        self.act_theme.setShortcut(QtGui.QKeySequence("Ctrl+T"))
        self.act_theme.triggered.connect(self._toggle_theme)

        self.act_validate = QtGui.QAction("Validate KML", self)
        self.act_validate.triggered.connect(self._validate)

        self.act_quit = QtGui.QAction("Quit", self)
        self.act_quit.setShortcut(QtGui.QKeySequence.Quit)
        self.act_quit.triggered.connect(self.close)

        self.act_refresh_map = QtGui.QAction("Refresh Map", self)
        self.act_refresh_map.setShortcut(QtGui.QKeySequence("Ctrl+R"))
        self.act_refresh_map.triggered.connect(self._refresh_map)

    def _make_menus_and_toolbar(self):
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.act_open)
        file_menu.addSeparator()
        file_menu.addAction(self.act_save)
        file_menu.addAction(self.act_save_as)
        file_menu.addSeparator()
        file_menu.addAction(self.act_export)
        file_menu.addSeparator()
        file_menu.addAction(self.act_quit)

        edit_menu = self.menuBar().addMenu("&Edit")
        edit_menu.addAction(self.act_undo)
        edit_menu.addAction(self.act_redo)

        tools_menu = self.menuBar().addMenu("&Tools")
        tools_menu.addAction(self.act_validate)
        tools_menu.addAction(self.act_refresh_map)

        view_menu = self.menuBar().addMenu("&View")
        view_menu.addAction(self.act_theme)

        tb = QtWidgets.QToolBar("Main", self)
        tb.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        tb.setIconSize(QtCore.QSize(28, 28))
        self.addToolBar(tb)
        for act in [self.act_open, self.act_save, self.act_export, self.act_undo, self.act_redo, self.act_theme]:
            tb.addAction(act)

    def _apply_default_styles(self):
        self.setStyleSheet("""
        QTreeWidget::item:selected { background: #D0E7FF; }
        *:focus { outline: 2px solid #0078D4; outline-offset: 1px; }
        QToolBar QToolButton { padding: 6px 10px; margin: 2px; }
        QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QPushButton { min-height: 28px; }
        """)

    def _toggle_theme(self, checked: bool):
        if checked:
            self.setStyleSheet("""
                QWidget { background: #121212; color: #F1F1F1; }
                QLineEdit, QTextEdit, QPlainTextEdit, QComboBox { background: #1E1E1E; color: #FFFFFF; border: 1px solid #3A3A3A; }
                QPushButton { background: #2A2A2A; border: 1px solid #4A4A4A; }
                QTreeWidget::item:selected { background: #334155; color: #FFFFFF; }
                *:focus { outline: 2px solid #22D3EE; }
            """)
        else:
            self._apply_default_styles()

    def _install_log_handler(self):
        class QtLogHandler(QtCore.QObject):
            sig = QtCore.Signal(str)
            def __init__(self, console):
                super().__init__()
                self.console = console
                self.sig.connect(self._append)
            def emit(self, record):
                self.sig.emit(record)
            def _append(self, msg):
                self.console.appendPlainText(msg)

        from ..core.utils import install_qt_console_handler
        install_qt_console_handler(QtLogHandler(self.log_console))

    def _open_kmz(self):
        path = open_kmz_dialog(self)
        if not path: return
        try:
            with NonBlockingProgress(self, "Opening KMZ…", "Parsing…") as prog:
                prog.set_range(0,0)
                doc = kmz_io.load_kmz(path)
        except Exception as e:
            self.logger.exception("Open KMZ failed")
            error_message(self, "Failed to open KMZ", str(e))
            return
        self.current_doc = doc
        self.current_kmz_path = path
        self.tree_panel.load_document(doc)
        self._refresh_map()
        info_message(self, "Opened", f"Loaded: {Path(path).name}")
        self.setWindowTitle(f"KMZ Studio — {Path(path).name}")

    def _refresh_map(self):
        if not self.current_doc: return
        visible_nodes = self.tree_panel.visible_nodes()
        html = map_renderer.render_folium_html(self.current_doc, visible_nodes)
        self.map_view.set_html(html)

    def _on_visibility_changed(self):
        self._refresh_map()

    def _on_node_selected(self, node):
        self.props_panel.bind_node(node)

    def _apply_properties(self, payload: dict):
        if not self.current_doc: return
        node = payload.get("node")
        if not node: return
        new_name = payload.get("name")
        if new_name is not None and new_name != node.name:
            cmd = NameEditCommand(node=node, new_name=new_name, tree_panel=self.tree_panel)
            self.undo_stack.push(cmd)
            self._refresh_map()

    def _save_kmz(self, save_as: bool=False):
        if not self.current_doc:
            warn_message(self, "Nothing to save", "Open a KMZ first.")
            return
        out_path = self.current_kmz_path
        if save_as or not out_path:
            out_path = save_file_dialog(self, caption="Save KMZ As", filter_str="KMZ files (*.kmz)")
            if not out_path: return
            if not out_path.lower().endswith(".kmz"):
                out_path += ".kmz"
            if os.path.exists(out_path) and not confirm_overwrite(self, out_path):
                return
        try:
            with NonBlockingProgress(self, "Saving KMZ…", "Writing…", determinate=True) as prog:
                prog.set_range(0,100)
                kmz_io.save_kmz(self.current_doc, out_path, progress=prog)
            info_message(self, "Saved", f"Wrote: {Path(out_path).name}")
            self.current_kmz_path = out_path
            self.setWindowTitle(f"KMZ Studio — {Path(out_path).name}")
        except Exception as e:
            self.logger.exception("Save KMZ failed")
            error_message(self, "Save failed", str(e))

    def _export_selected(self):
        if not self.current_doc:
            warn_message(self, "Nothing to export", "Open a KMZ first.")
            return
        nodes = self.tree_panel.checked_nodes()
        if not nodes:
            warn_message(self, "No items selected", "Use the checkboxes to select items to export.")
            return
        choice, out_path = export_selected_dialog(self)
        if not out_path: return
        try:
            if choice == "kml":
                exporters.export_to_kml(nodes, out_path)
                info_message(self, "Exported", f"KML written:\n{out_path}")
            elif choice == "csv":
                exporters.export_to_csv(nodes, out_path)
                info_message(self, "Exported", f"CSV written:\n{out_path}")
        except Exception as e:
            self.logger.exception("Export failed")
            error_message(self, "Export failed", str(e))

    def _validate(self):
        if not self.current_doc:
            warn_message(self, "Nothing to validate", "Open a KMZ first.")
            return
        from ..core.validate import validate_document
        issues = validate_document(self.current_doc)
        if not issues:
            info_message(self, "Validation", "No issues found.")
        else:
            msg = "\n".join(f"• {it}" for it in issues[:200])
            warn_message(self, "Validation issues", msg)
