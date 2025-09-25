import sys
import types
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Provide a lightweight stub for the PySide6 module used by the production
# code so the tests do not require Qt libraries to be present.
if "PySide6" not in sys.modules:
    class _Signal:
        def connect(self, *_args, **_kwargs):
            pass

    class _QProgressDialog:
        def __init__(self, *_args, **_kwargs):
            self.canceled = _Signal()

        def setWindowTitle(self, *_args, **_kwargs):
            pass

        def setWindowModality(self, *_args, **_kwargs):
            pass

        def setAutoClose(self, *_args, **_kwargs):
            pass

        def setAutoReset(self, *_args, **_kwargs):
            pass

        def setMinimumDuration(self, *_args, **_kwargs):
            pass

        def setRange(self, *_args, **_kwargs):
            pass

        def show(self):
            pass

        def close(self):
            pass

        def reset(self):
            pass

    class _QMessageBox:
        @staticmethod
        def information(*_args, **_kwargs):
            pass

        @staticmethod
        def warning(*_args, **_kwargs):
            pass

        @staticmethod
        def critical(*_args, **_kwargs):
            pass

    qtwidgets = types.SimpleNamespace(
        QProgressDialog=_QProgressDialog,
        QMessageBox=_QMessageBox,
    )
    qtcore = types.SimpleNamespace(Qt=types.SimpleNamespace(WindowModal=None))
    pyside6 = types.ModuleType("PySide6")
    pyside6.QtWidgets = qtwidgets
    pyside6.QtCore = qtcore
    sys.modules["PySide6"] = pyside6

from kmz_studio.core.kml_model import KMLDocument, KMLNode, KMLNodeType
from kmz_studio.core.kmz_io import document_to_kml_bytes


def _nsmap(root_tag: str) -> dict[str, str]:
    if root_tag.startswith("{") and "}" in root_tag:
        uri = root_tag.split("}", 1)[0][1:]
        return {"kml": uri}
    return {"kml": ""}


def test_nested_folders_are_preserved_in_serialised_kml():
    doc = KMLDocument()
    root = KMLNode(type=KMLNodeType.DOCUMENT, name="Root")
    parent = KMLNode(type=KMLNodeType.FOLDER, name="Parent")
    child = KMLNode(type=KMLNodeType.FOLDER, name="Child")
    placemark = KMLNode(type=KMLNodeType.PLACEMARK, name="Place")

    child.add_child(placemark)
    parent.add_child(child)
    root.add_child(parent)
    doc.root = root
    doc.index()

    xml_bytes = document_to_kml_bytes(doc)
    root_el = ET.fromstring(xml_bytes)
    ns = _nsmap(root_el.tag)

    folders = root_el.findall(".//kml:Folder", ns)
    names = {el.findtext("kml:name", default="", namespaces=ns): el for el in folders}
    parent_folder = names["Parent"]
    child_names = {
        el.findtext("kml:name", default="", namespaces=ns)
        for el in parent_folder.findall("kml:Folder", ns)
    }

    assert "Child" in child_names, "Child folder should be nested under Parent folder"
