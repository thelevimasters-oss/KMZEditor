from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any
from shapely.geometry import Point, LineString, Polygon, shape
from fastkml import kml


def to_shapely_geometry(g):
    """Return a Shapely geometry from various geometry-like inputs."""
    if g is None:
        return None
    if hasattr(g, "geom_type") and hasattr(g, "wkt"):
        return g
    if hasattr(g, "geometry"):
        try:
            return to_shapely_geometry(getattr(g, "geometry"))
        except Exception:
            pass
    if hasattr(g, "__geo_interface__"):
        try:
            return shape(g.__geo_interface__)
        except Exception:
            pass
    try:
        if isinstance(g, (tuple, list)) and len(g) >= 2:
            return Point(float(g[0]), float(g[1]))
    except Exception:
        pass
    return None

class KMLNodeType(Enum):
    DOCUMENT = "Document"
    FOLDER = "Folder"
    PLACEMARK = "Placemark"
    STYLE = "Style"
    OVERLAY = "Overlay"
    NETWORKLINK = "NetworkLink"

def _gen_id(prefix="id"): return f"{prefix}-{uuid.uuid4().hex[:12]}"

@dataclass
class KMLNode:
    type: KMLNodeType
    id: str = field(default_factory=lambda: _gen_id("node"))
    name: str | None = None
    description: str | None = None
    style_url: str | None = None
    geometry: Any | None = None
    children: List['KMLNode'] = field(default_factory=list)
    parent: Optional['KMLNode'] = None
    visible: bool = True
    properties: Dict[str, Any] = field(default_factory=dict)
    def add_child(self, ch:'KMLNode'): ch.parent = self; self.children.append(ch)
    def is_placemark(self): return self.type == KMLNodeType.PLACEMARK

@dataclass
class KMLDocument:
    root: Optional[KMLNode] = None
    id_map: Dict[str, KMLNode] = field(default_factory=dict)
    styles: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    def index(self):
        self.id_map.clear()
        def visit(n: KMLNode):
            self.id_map[n.id] = n
            for c in n.children: visit(c)
        if self.root: visit(self.root)

def _from_fastkml_feature(feat, parent_node: KMLNode | None, doc: KMLDocument) -> KMLNode | None:
    if isinstance(feat, kml.Document):
        node = KMLNode(type=KMLNodeType.DOCUMENT, id=getattr(feat,"id",None) or _gen_id("doc"), name=feat.name, description=feat.description)
    elif isinstance(feat, kml.Folder):
        node = KMLNode(type=KMLNodeType.FOLDER, id=getattr(feat,"id",None) or _gen_id("folder"), name=feat.name, description=feat.description)
    elif isinstance(feat, kml.Placemark):
        geom = to_shapely_geometry(feat.geometry)
        node = KMLNode(type=KMLNodeType.PLACEMARK, id=getattr(feat,"id",None) or _gen_id("pm"), name=feat.name, description=feat.description, geometry=geom, style_url=getattr(feat, "styleUrl", None))
    else:
        node = KMLNode(type=KMLNodeType.FOLDER, id=getattr(feat,"id",None) or _gen_id("folder"), name=getattr(feat,"name",None), description=getattr(feat,"description",None))
    if hasattr(feat, "features"):
        for sub in list(feat.features()):
            ch = _from_fastkml_feature(sub, node, doc)
            if ch: node.add_child(ch)
    return node

def parse_kml_bytes(data: bytes) -> KMLDocument:
    doc = KMLDocument()
    k = kml.KML()
    k.from_string(data)
    root = None
    for d in k.features():
        root = _from_fastkml_feature(d, None, doc); break
    if root is None:
        root = KMLNode(type=KMLNodeType.DOCUMENT, id=_gen_id("doc"), name="Document")
        for f in k.features():
            ch = _from_fastkml_feature(f, root, doc)
            if ch: root.add_child(ch)
    doc.root = root
    doc.index()
    return doc
