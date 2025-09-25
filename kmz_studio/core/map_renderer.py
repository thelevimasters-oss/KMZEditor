import folium
from shapely.geometry import Point, LineString, Polygon
from .kml_model import KMLDocument, KMLNode, KMLNodeType

def _collect_visible_placemarks(nodes):
    out=[]
    def visit(n):
        if not n.visible: return
        if n.type==KMLNodeType.PLACEMARK: out.append(n)
        for c in n.children: visit(c)
    for n in nodes: visit(n)
    return out

def _initial_loc(placemarks):
    for pm in placemarks:
        g=pm.geometry
        try:
            if hasattr(g, 'geom_type') and g.geom_type == 'Point':
                return [float(g.y), float(g.x)]
            if g is not None and hasattr(g, 'centroid'):
                c = g.centroid
                return [float(c.y), float(c.x)]
        except Exception:
            pass
    return [0.0, 0.0]

def render_folium_html(doc: KMLDocument, visible_nodes):
    placemarks=_collect_visible_placemarks(visible_nodes)
    loc=_initial_loc(placemarks)
    m=folium.Map(location=loc, zoom_start=3, control_scale=True, prefer_canvas=True)
    grp=folium.FeatureGroup(name="Placemarks", show=True)
    for pm in placemarks:
        g=pm.geometry
        name=pm.name or "(unnamed)"
        popup=folium.Popup(html=f"<b>{name}</b>", max_width=300)
        if g is None: continue
        try:
            if hasattr(g, 'geom_type') and g.geom_type == 'Point':
                folium.Marker([float(g.y), float(g.x)], popup=popup).add_to(grp)
            elif hasattr(g, 'geom_type') and g.geom_type == 'LineString' and hasattr(g, 'coords'):
                folium.PolyLine([[float(y),float(x)] for (x,y) in g.coords], weight=3, opacity=0.9, popup=popup).add_to(grp)
            elif hasattr(g, 'geom_type') and g.geom_type == 'Polygon' and hasattr(g, 'exterior'):
                folium.Polygon([[float(y),float(x)] for (x,y) in g.exterior.coords], weight=2, fill=True, fill_opacity=0.2, popup=popup).add_to(grp)
            elif hasattr(g, 'centroid'):
                c = g.centroid; folium.Marker([float(c.y), float(c.x)], popup=popup).add_to(grp)
        except Exception:
            pass
    grp.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    return m.get_root().render()
