from PyQt6.QtCore import Qt, QByteArray
from PyQt6.QtGui import QPixmap, QIcon, QPainter
from PyQt6.QtSvg import QSvgRenderer

SVG_SEARCH = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">
  <circle cx="11" cy="11" r="7" stroke="{color}" stroke-width="2"/>
  <line x1="16.5" y1="16.5" x2="21" y2="21" stroke="{color}" stroke-width="2"
        stroke-linecap="round"/>
</svg>
"""

SVG_DOWNLOAD = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">
  <path d="M12 3v13" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
  <path d="M7 11l5 5 5-5" stroke="{color}" stroke-width="2"
        stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M4 20h16" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
</svg>
"""

SVG_HISTORY = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">
  <circle cx="12" cy="12" r="9" stroke="{color}" stroke-width="2"/>
  <path d="M12 7v5l3 3" stroke="{color}" stroke-width="2"
        stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""

SVG_SETTINGS = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">
  <circle cx="12" cy="12" r="3" stroke="{color}" stroke-width="2"/>
  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83
           l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21
           a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33
           l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15
           a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9
           a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06
           A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0
           v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06
           a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9
           a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"
        stroke="{color}" stroke-width="2"/>
</svg>
"""


def svg_icon(template: str, color: str, size: int = 22) -> QIcon:
    """Render an SVG template string (with {color} placeholder) into a QIcon."""
    data = QByteArray(template.replace("{color}", color).encode())
    renderer = QSvgRenderer(data)
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    renderer.render(painter)
    painter.end()
    return QIcon(pix)

__all__ = ["SVG_SEARCH", "SVG_DOWNLOAD", "SVG_HISTORY", "SVG_SETTINGS", "svg_icon"]
