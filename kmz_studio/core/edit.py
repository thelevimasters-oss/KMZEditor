from PySide6 import QtGui
from .kml_model import KMLNode
from .utils import get_logger
logger = get_logger()

class NameEditCommand(QtGui.QUndoCommand):
    def __init__(self, node: KMLNode, new_name: str, tree_panel):
        super().__init__(f"Rename '{node.name}' → '{new_name}'")
        self.node=node; self.new_name=new_name; self.old_name=node.name; self.tree_panel=tree_panel
    def redo(self):
        self.node.name=self.new_name
        self.tree_panel.rename_node_in_ui(self.node)
        logger.info("Renamed node %s to %s", self.node.id, self.new_name)
    def undo(self):
        self.node.name=self.old_name
        self.tree_panel.rename_node_in_ui(self.node)
        logger.info("Undo rename node %s to %s", self.node.id, self.old_name)
