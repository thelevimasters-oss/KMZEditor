from .kml_model import KMLDocument, KMLNodeType
def validate_document(doc: KMLDocument) -> list[str]:
    issues=[]
    if not doc.root: issues.append("Empty document."); return issues
    def visit(n):
        if n.type==KMLNodeType.PLACEMARK:
            if n.style_url and not (n.style_url.startswith("#") or n.style_url.startswith("http")):
                issues.append(f"Placemark '{n.name or n.id}' has suspicious styleUrl: {n.style_url}")
        for c in n.children: visit(c)
    visit(doc.root); return issues
