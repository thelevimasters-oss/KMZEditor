from PySide6 import QtCore, QtWidgets
from ..core.kml_model import KMLNode, KMLNodeType

class PropertiesPanel(QtWidgets.QWidget):
    applyRequested = QtCore.Signal(dict)
    def __init__(self, parent=None):
        super().__init__(parent)
        self._node: KMLNode | None = None

        self.title = QtWidgets.QLabel("<b>Properties</b>")
        self.name = QtWidgets.QLineEdit()
        self.name.setPlaceholderText("Name")
        self.desc = QtWidgets.QTextEdit()
        self.desc.setPlaceholderText("Description (HTML allowed)")

        self.type_label = QtWidgets.QLabel("—")
        self.id_label = QtWidgets.QLabel("—")
        self.geom_label = QtWidgets.QLabel("—")

        self.btn_apply = QtWidgets.QPushButton("Apply")
        self.btn_apply.setDefault(True)
        self.btn_apply.clicked.connect(self._apply)

        form = QtWidgets.QFormLayout()
        form.addRow(self.title)
        form.addRow("Type:", self.type_label)
        form.addRow("ID:", self.id_label)
        form.addRow("Geometry:", self.geom_label)
        form.addRow("Name:", self.name)
        form.addRow("Description:", self.desc)
        form.addRow(self.btn_apply)
        self.setLayout(form)

    def bind_node(self, node: KMLNode | None):
        self._node = node
        if node is None:
            self.title.setText("<b>Properties</b>")
            self.name.setText("")
            self.desc.setPlainText("")
            self.type_label.setText("—")
            self.id_label.setText("—")
            self.geom_label.setText("—")
            self.setDisabled(True)
            return
        self.setDisabled(False)
        self.title.setText(f"<b>Properties — {node.name or '(unnamed)'} </b>")
        self.name.setText(node.name or "")
        self.desc.setPlainText(node.description or "")
        self.type_label.setText(node.type.value)
        self.id_label.setText(node.id or "—")
        self.geom_label.setText(node.geometry.geom_type if node.geometry is not None else "None")

    def _apply(self):
        if not self._node: return
        self.applyRequested.emit({"node": self._node, "name": self.name.text().strip(), "description": self.desc.toPlainText().strip()})
