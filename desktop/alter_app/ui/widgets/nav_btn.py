from PyQt6.QtWidgets import QToolButton, QSizePolicy
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont

from ...theme import P
from ...utils.icons import svg_icon

class NavBtn(QToolButton):
    def __init__(self, svg_template: str, text: str):
        super().__init__()
        self._svg = svg_template
        self.setCheckable(True)
        self.setFixedHeight(56)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.setIconSize(QSize(22, 22))
        self.setText(text)
        self.setFont(QFont("Segoe UI", 8))
        self._apply_color(P["muted"])
        self.toggled.connect(
            lambda chk: self._apply_color(P["accent"] if chk else P["muted"])
        )
        self.setStyleSheet(f"""
            QToolButton {{
                background: transparent; border: none;
                color: {P['muted']}; font-size: 8pt;
                padding: 2px 0px;
            }}
            QToolButton:hover {{ color: {P['text']}; }}
            QToolButton:checked {{ color: {P['accent']}; font-weight: 700; }}
        """)

    def _apply_color(self, color: str):
        self.setIcon(svg_icon(self._svg, color))
        self.setStyleSheet(f"""
            QToolButton {{
                background: transparent; border: none;
                color: {color}; font-size: 8pt;
                padding: 2px 0px;
            }}
            QToolButton:hover {{ color: {P['text']}; }}
            QToolButton:checked {{ color: {P['accent']}; font-weight: 700; }}
        """)
