from __future__ import annotations
import zipfile
from pathlib import Path
from typing import Optional
from .kml_model import KMLDocument, KMLNode, KMLNodeType, parse_kml_bytes
from .utils import get_logger
import simplekml

logger = get_logger()

def _find_primary_kml(z: zipfile.ZipFile) -> Optional[str]:
    names = z.namelist()
    for cand in ("doc.kml","Doc.kml","kml/doc.kml"):
        if cand in names: return cand
    kmls = [n for n in names if n.lower().endswith(".kml")]
    return kmls[0] if kmls else None

def load_kmz(path: str) -> KMLDocument:
    p = Path(path)
    if p.suffix.lower() == ".kml":
        return parse_kml_bytes(p.read_bytes())
    with zipfile.ZipFile(path, "r") as z:
        prim = _find_primary_kml(z)
        if not prim: raise ValueError("No .kml file found inside KMZ.")
        data = z.read(prim)
    return parse_kml_bytes(data)

def _write_node_to_simplekml(kml_doc: simplekml.Kml, parent_folder, node: KMLNode):
    if node.type in (KMLNodeType.FOLDER, KMLNodeType.DOCUMENT):
        container = parent_folder if parent_folder is not None else kml_doc
        if node.type == KMLNodeType.DOCUMENT:
            folder = container.newdocument(name=(node.name or ""))
        else:
            folder = container.newfolder(name=(node.name or ""))
        if node.description:
            folder.description = node.description
        for ch in node.children:
            _write_node_to_simplekml(kml_doc, folder, ch)
        return
    if node.type == KMLNodeType.PLACEMARK:
        g = node.geometry
        if g is None:
            p = kml_doc.newpoint(name=(node.name or ""))
        else:
            t = g.geom_type
            if t == "Point":
                p = kml_doc.newpoint(name=(node.name or ""), coords=[(float(g.x), float(g.y))])
            elif t == "LineString":
                p = kml_doc.newlinestring(name=(node.name or ""), coords=[(float(x),float(y)) for x,y in g.coords])
            elif t == "Polygon":
                p = kml_doc.newpolygon(name=(node.name or ""), outerboundaryis=[(float(x),float(y)) for x,y in g.exterior.coords])
            else:
                c = g.centroid
                p = kml_doc.newpoint(name=(node.name or ""), coords=[(float(c.x), float(c.y))])
        if node.description: p.description = node.description
        if node.style_url: p.styleurl = node.style_url

def document_to_kml_bytes(doc: KMLDocument) -> bytes:
    k = simplekml.Kml()
    if doc.root:
        _write_node_to_simplekml(k, None, doc.root)
    else:
        k.newdocument(name="Document")
    return k.kml().encode("utf-8")

def save_kmz(doc: KMLDocument, out_path: str, progress=None):
    if progress: progress.setValue(10)
    data = document_to_kml_bytes(doc)
    if progress: progress.setValue(40)
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("doc.kml", data)
    if progress: progress.setValue(100)
    logger.info("KMZ saved: %s", out_path)
