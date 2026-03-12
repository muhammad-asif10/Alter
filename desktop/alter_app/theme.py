P_DARK = {
    "bg":           "#111111",
    "surface":      "#1A1A1A",
    "card":         "#1E1E1E",
    "card_hover":   "#252525",
    "accent":       "#2383E2",
    "accent_h":     "#1C6EC7",
    "text":         "#E8E8E8",
    "muted":        "#9A9A9A",
    "success":      "#22C55E",
    "error":        "#EF4444",
    "warning":      "#F59E0B",
    "border":       "#2A2A2A",
    "purple":       "#A855F7",
    "cyan":         "#22D3EE",
}
P_LIGHT = {
    "bg":           "#F7F7F7",
    "surface":      "#EEEEEE",
    "card":         "#FFFFFF",
    "card_hover":   "#F0F2F5",
    "accent":       "#2383E2",
    "accent_h":     "#1C6EC7",
    "text":         "#111111",
    "muted":        "#666666",
    "success":      "#16A34A",
    "error":        "#DC2626",
    "warning":      "#D97706",
    "border":       "#DEDEDE",
    "purple":       "#9333EA",
    "cyan":         "#0891B2",
}
P = dict(P_DARK)  # active palette — mutated on theme change

def build_qss(p: dict) -> str:
    return f"""
* {{
    font-family: "Segoe UI", -apple-system, "SF Pro Text", sans-serif;
    font-size: 9pt;
    color: {p['text']};
}}
QMainWindow, QWidget {{
    background-color: {p['bg']};
}}
QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollBar:vertical {{
    background: {p['bg']};
    width: 4px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {p['border']};
    border-radius: 2px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
QLineEdit {{
    background-color: {p['card']};
    color: {p['text']};
    border: 1px solid {p['border']};
    border-radius: 18px;
    padding: 9px 14px;
    selection-background-color: {p['accent']};
    font-size: 9pt;
}}
QLineEdit:focus {{ border-color: {p['accent']}; }}
QComboBox {{
    background-color: {p['card']};
    color: {p['text']};
    border: 1px solid {p['border']};
    border-radius: 8px;
    padding: 5px 10px;
    min-height: 30px;
    font-size: 9pt;
}}
QComboBox::drop-down {{ border: none; width: 20px; }}
QComboBox::down-arrow {{ width: 8px; height: 8px; }}
QComboBox QAbstractItemView {{
    background: {p['surface']};
    color: {p['text']};
    border: 1px solid {p['border']};
    selection-background-color: {p['accent']};
    outline: none;
}}
QCheckBox {{
    color: {p['muted']};
    spacing: 6px;
    font-size: 8pt;
}}
QCheckBox::indicator {{
    width: 14px; height: 14px;
    border-radius: 3px;
    border: 1px solid {p['border']};
    background: {p['card']};
}}
QCheckBox::indicator:checked {{
    background: {p['accent']};
    border-color: {p['accent']};
}}
QCheckBox:hover {{ color: {p['text']}; }}
QProgressBar {{
    background-color: {p['border']};
    border-radius: 2px;
    border: none;
}}
QProgressBar::chunk {{
    background-color: {p['accent']};
    border-radius: 2px;
}}
QFrame#card {{
    background-color: {p['card']};
    border-radius: 12px;
    border: 1px solid {p['border']};
}}
QFrame#bottombar {{
    background-color: {p['surface']};
    border-top: 1px solid {p['border']};
}}
QLabel {{ background: transparent; }}
QPushButton {{ border: none; border-radius: 8px; padding: 7px 14px; }}
"""

QSS = build_qss(P)

__all__ = ["P_DARK", "P_LIGHT", "P", "build_qss", "QSS"]
