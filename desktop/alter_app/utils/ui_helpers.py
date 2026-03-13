from PyQt6.QtWidgets import QLabel, QPushButton, QFrame
from PyQt6.QtGui import QFont
from ..theme import P

def lbl(text="", size=10, bold=False, color=None) -> QLabel:
    w = QLabel(text)
    f = QFont("Segoe UI", size)
    f.setBold(bold)
    w.setFont(f)
    if color:
        w.setStyleSheet(f"color: {color};")
    return w


def btn(text, bg, fg="#fff", hover=None) -> QPushButton:
    h = hover or bg
    b = QPushButton(text)
    b.setStyleSheet(f"""
        QPushButton {{
            background: {bg}; color: {fg};
            border-radius: 8px; padding: 9px 20px;
            font-weight: 600; border: none;
        }}
        QPushButton:hover {{ background: {h}; }}
        QPushButton:disabled {{
            background: {P['surface']};
            color: {P['muted']};
            border: 1px solid {P['border']};
        }}
    """)
    return b


def hsep() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet(f"background: {P['border']}; max-height: 1px; border: none;")
    return f

__all__ = ["lbl", "btn", "hsep"]
