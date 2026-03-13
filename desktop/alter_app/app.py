import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor, QIcon

from .main_window import MainWindow
from .theme import P, set_system_is_light
from .constants import resolve_app_icon_path

def main():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "alter.desktop.app"
            )
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("Alter")

    icon_path = resolve_app_icon_path()
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Detect the OS light/dark preference from the default system palette
    # BEFORE we override it with our own custom palette.
    _sys_is_light = app.palette().color(QPalette.ColorRole.Window).lightness() > 128
    set_system_is_light(_sys_is_light)

    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window,          QColor(P["bg"]))
    pal.setColor(QPalette.ColorRole.WindowText,      QColor(P["text"]))
    pal.setColor(QPalette.ColorRole.Base,            QColor(P["card"]))
    pal.setColor(QPalette.ColorRole.AlternateBase,   QColor(P["surface"]))
    pal.setColor(QPalette.ColorRole.Text,            QColor(P["text"]))
    pal.setColor(QPalette.ColorRole.Button,          QColor(P["card"]))
    pal.setColor(QPalette.ColorRole.ButtonText,      QColor(P["text"]))
    pal.setColor(QPalette.ColorRole.Highlight,       QColor(P["accent"]))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#fff"))
    app.setPalette(pal)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
