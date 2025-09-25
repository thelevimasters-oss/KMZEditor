from PySide6 import QtCore, QtWidgets
from ..core.kml_model import KMLNode, KMLNodeType, KMLDocument

class KMLTreePanel(QtWidgets.QWidget):
    nodeSelectionChanged = QtCore.Signal(object)
    visibilityChanged = QtCore.Signal()
    requestRefreshMap = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.doc: KMLDocument | None = None
        # Use node.id (string) as the key to avoid 'unhashable type: KMLNode'
        self._node_to_item: dict[str, QtWidgets.QTreeWidgetItem] = {}
        self._item_to_node: dict[QtWidgets.QTreeWidgetItem, KMLNode] = {}

        self.search = QtWidgets.QLineEdit(self)
        self.search.setPlaceholderText("Search (name contains)…")
        self.search.textChanged.connect(self._filter_tree)

        self.tree = QtWidgets.QTreeWidget(self)
        self.tree.setHeaderLabels(["Name", "Type"])
        self.tree.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tree.setUniformRowHeights(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setAnimated(True)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)
        self.tree.itemChanged.connect(self._on_item_changed)
        self.tree.setExpandsOnDoubleClick(True)
        self.tree.setAllColumnsShowFocus(True)
        self.tree.setColumnWidth(0, 220)

        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(self.search)
        lay.addWidget(self.tree)

        self.tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)

    def load_document(self, doc: KMLDocument):
        self.doc = doc
        self.tree.blockSignals(True)
        self.tree.clear()
        self._node_to_item.clear()
        self._item_to_node.clear()
        if doc.root:
            root_item = self._add_node_recursive(doc.root, None)
            self.tree.addTopLevelItem(root_item)
            root_item.setExpanded(True)
        self.tree.blockSignals(False)
        self.requestRefreshMap.emit()

    def _add_node_recursive(self, node: KMLNode, parent_item):
        item = QtWidgets.QTreeWidgetItem()
        item.setText(0, node.name or "(unnamed)")
        item.setText(1, node.type.value)
        item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
        item.setCheckState(0, QtCore.Qt.Checked if node.visible else QtCore.Qt.Unchecked)
        self._node_to_item[node.id] = item
        self._item_to_node[item] = node
        for ch in node.children:
            child_item = self._add_node_recursive(ch, item)
            item.addChild(child_item)
        return item

    def _filter_tree(self, text: str):
        text = text.lower().strip()
        it = QtWidgets.QTreeWidgetItemIterator(self.tree)
        while it.value():
            item = it.value()
            node = self._item_to_node.get(item)
            if node is not None:
                match = (not text) or (node.name and text in node.name.lower())
                item.setHidden(not match)
            it += 1

    def _on_selection_changed(self):
        items = self.tree.selectedItems()
        if not items:
            self.nodeSelectionChanged.emit(None); return
        node = self._item_to_node.get(items[0])
        self.nodeSelectionChanged.emit(node)

    def _on_item_changed(self, item, column):
        if column == 0:
            node = self._item_to_node.get(item)
            if node is not None:
                node.visible = (item.checkState(0) == QtCore.Qt.Checked)
                self.visibilityChanged.emit()

    def checked_nodes(self):
        out = []
        it = QtWidgets.QTreeWidgetItemIterator(self.tree)
        while it.value():
            item = it.value()
            if item.checkState(0) == QtCore.Qt.Checked:
                node = self._item_to_node.get(item)
                if node and node.type in (KMLNodeType.PLACEMARK, KMLNodeType.FOLDER):
                    out.append(node)
            it += 1
        return out

    def visible_nodes(self):
        out = []
        it = QtWidgets.QTreeWidgetItemIterator(self.tree)
        while it.value():
            item = it.value()
            if not item.isHidden():
                node = self._item_to_node.get(item)
                if node and node.visible:
                    out.append(node)
            it += 1
        return out

    def rename_node_in_ui(self, node: KMLNode):
        item = self._node_to_item.get(node.id)
        if item:
            item.setText(0, node.name or "(unnamed)")

    def _show_context_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        act_expand = menu.addAction("Expand all")
        act_collapse = menu.addAction("Collapse all")
        act_check = menu.addAction("Check visible")
        act_uncheck = menu.addAction("Uncheck all")
        chosen = menu.exec(self.tree.viewport().mapToGlobal(pos))
        if chosen == act_expand:
            self.tree.expandAll()
        elif chosen == act_collapse:
            self.tree.collapseAll()
        elif chosen == act_check:
            it = QtWidgets.QTreeWidgetItemIterator(self.tree)
            while it.value():
                item = it.value()
                if not item.isHidden():
                    item.setCheckState(0, QtCore.Qt.Checked)
                it += 1
            self.visibilityChanged.emit()
        elif chosen == act_uncheck:
            it = QtWidgets.QTreeWidgetItemIterator(self.tree)
            while it.value():
                item = it.value()
                item.setCheckState(0, QtCore.Qt.Unchecked)
                it += 1
            self.visibilityChanged.emit()
