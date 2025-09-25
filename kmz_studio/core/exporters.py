import csv
from pathlib import Path
import simplekml
from .kml_model import KMLNode, KMLNodeType

def _enumerate_placemarks(nodes):
    out = []
    def visit(n):
        if n.type == KMLNodeType.PLACEMARK: out.append(n)
        for c in n.children: visit(c)
    for n in nodes: visit(n)
    return out

def export_to_kml(nodes, out_path: str):
    k = simplekml.Kml()
    folder = k.newfolder(name="Export")
    for pm in _enumerate_placemarks(nodes):
        g = pm.geometry
        if g is None:
            p = folder.newpoint(name=(pm.name or ""))
        else:
            if g.geom_type == "Point":
                p = folder.newpoint(name=(pm.name or ""), coords=[(g.x, g.y)])
            elif g.geom_type == "LineString":
                p = folder.newlinestring(name=(pm.name or ""), coords=list(g.coords))
            elif g.geom_type == "Polygon":
                p = folder.newpolygon(name=(pm.name or ""), outerboundaryis=list(g.exterior.coords))
            else:
                c = g.centroid
                p = folder.newpoint(name=(pm.name or ""), coords=[(c.x, c.y)])
        if pm.description: p.description = pm.description
        if pm.style_url: p.styleurl = pm.style_url
    Path(out_path).write_bytes(k.kml().encode("utf-8"))

def export_to_csv(nodes, out_path: str):
    pms = _enumerate_placemarks(nodes)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id","name","description","geometry_type","lon","lat"])
        for pm in pms:
            lon=lat=gtype=""
            if pm.geometry is not None and pm.geometry.geom_type=="Point":
                lon=f"{pm.geometry.x:.8f}"; lat=f"{pm.geometry.y:.8f}"; gtype="Point"
            elif pm.geometry is not None:
                gtype = pm.geometry.geom_type
            w.writerow([pm.id, pm.name or "", pm.description or "", gtype, lon, lat])
