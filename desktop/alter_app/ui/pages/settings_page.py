import shutil
from typing import Dict

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea, QFrame, QLabel, QFileDialog, QComboBox, QLineEdit, QSizePolicy, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal

from ...theme import P
from ...constants import APP_VERSION
from ...data.settings import Settings
from ...utils.ui_helpers import lbl, btn, hsep

class SettingsPage(QWidget):
    sig_theme = pyqtSignal(str)  # emits: "dark" | "light" | "system"

    def __init__(self, settings: Settings):
        super().__init__()
        self._s = settings

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 14, 12, 10)
        root.setSpacing(10)

        root.addWidget(lbl("Settings", 14, bold=True))
        root.addWidget(hsep())

        # Scroll everything so all settings fit on the small window
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        sl = QVBoxLayout(inner)
        sl.setSpacing(10)
        sl.setContentsMargins(0, 0, 4, 0)
        scroll.setWidget(inner)
        root.addWidget(scroll, 1)

        # ── Theme ──
        sl.addWidget(lbl("THEME", 9, bold=True, color=P["muted"]))
        theme_row = QHBoxLayout()
        theme_row.setSpacing(8)
        self._theme_btns: Dict[str, QPushButton] = {}
        current_theme = settings.get("theme")
        for key, label in [("dark", "Dark"), ("light", "Light"), ("system", "System")]:
            b = QPushButton(label)
            b.setCheckable(True)
            b.setChecked(key == current_theme)
            b.setFixedHeight(32)
            b.setStyleSheet(self._theme_pill(key == current_theme))
            b.clicked.connect(lambda _, k=key: self._set_theme(k))
            self._theme_btns[key] = b
            theme_row.addWidget(b)
        theme_row.addStretch()
        sl.addLayout(theme_row)
        sl.addWidget(hsep())

        # ── Save location ──
        sl.addWidget(lbl("SAVE LOCATION", 9, bold=True, color=P["muted"]))
        pr = QHBoxLayout()
        self._path_lbl = QLabel(settings.get("save_path"))
        self._path_lbl.setStyleSheet(
            f"background:{P['card']};border:1px solid {P['border']};"
            f"border-radius:8px;padding:9px 14px;"
        )
        self._br_btn = btn("Browse", P["card_hover"], P["text"])
        self._br_btn.setFixedWidth(88)
        self._br_btn.clicked.connect(self._browse)
        pr.addWidget(self._path_lbl, 1)
        pr.addWidget(self._br_btn)
        sl.addLayout(pr)

        # ── Max concurrent ──
        sl.addWidget(lbl("MAX CONCURRENT DOWNLOADS", 9, bold=True, color=P["muted"]))
        self._cc_box = QComboBox()
        self._cc_box.addItems(["1", "2", "3", "4", "5"])
        self._cc_box.setCurrentText(str(settings.get("max_dl")))
        self._cc_box.setFixedWidth(80)
        self._cc_box.currentTextChanged.connect(lambda v: settings.set("max_dl", int(v)))
        sl.addWidget(self._cc_box)
        sl.addWidget(hsep())

        # ── Filename Template (#9) ──
        sl.addWidget(lbl("FILENAME TEMPLATE", 9, bold=True, color=P["muted"]))
        self._tpl_edit = QLineEdit(settings.get("filename_tpl") or "%(title)s.%(ext)s")
        self._tpl_edit.setMinimumHeight(36)
        self._tpl_edit.textChanged.connect(lambda v: settings.set("filename_tpl", v))
        sl.addWidget(self._tpl_edit)
        # Preset buttons
        preset_row = QHBoxLayout()
        preset_row.setSpacing(6)
        for label, tpl in [
            ("Title", "%(title)s.%(ext)s"),
            ("Artist – Title", "%(uploader)s - %(title)s.%(ext)s"),
            ("Date – Title", "%(upload_date)s %(title)s.%(ext)s"),
        ]:
            pb = QPushButton(label)
            pb.setFixedHeight(28)
            pb.setStyleSheet(
                f"QPushButton{{background:{P['card_hover']};color:{P['muted']};"
                f"border-radius:6px;border:none;font-size:8pt;padding:2px 8px;}}"
                f"QPushButton:hover{{color:{P['text']};}}"
            )
            pb.clicked.connect(lambda _, t=tpl: (
                self._tpl_edit.setText(t),
                settings.set("filename_tpl", t),
            ))
            preset_row.addWidget(pb)
        preset_row.addStretch()
        sl.addLayout(preset_row)
        sl.addWidget(hsep())

        # ── Notification Preferences (#17) ──
        sl.addWidget(lbl("NOTIFICATIONS", 9, bold=True, color=P["muted"]))
        notify_row = QHBoxLayout()
        notify_row.setSpacing(8)
        self._notify_btns: Dict[str, QPushButton] = {}
        current_notify = settings.get("notify") or "each"
        for key, label in [("each", "Each"), ("batch", "Batch"), ("never", "Never")]:
            b = QPushButton(label)
            b.setCheckable(True)
            b.setChecked(key == current_notify)
            b.setFixedHeight(32)
            b.setStyleSheet(self._theme_pill(key == current_notify))
            b.clicked.connect(lambda _, k=key: self._set_notify(k))
            self._notify_btns[key] = b
            notify_row.addWidget(b)
        notify_row.addStretch()
        sl.addLayout(notify_row)
        sl.addWidget(hsep())

        # ── Speed Throttle (#11) ──
        sl.addWidget(lbl("SPEED LIMIT", 9, bold=True, color=P["muted"]))
        self._speed_box = QComboBox()
        _speed_opts = [
            ("Unlimited", 0),
            ("5 MB/s",   5120),
            ("2 MB/s",   2048),
            ("1 MB/s",   1024),
            ("500 KB/s",  500),
        ]
        for label, val in _speed_opts:
            self._speed_box.addItem(label, val)
        cur_speed = int(settings.get("speed_limit") or 0)
        for i in range(self._speed_box.count()):
            if self._speed_box.itemData(i) == cur_speed:
                self._speed_box.setCurrentIndex(i)
                break
        self._speed_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._speed_box.currentIndexChanged.connect(
            lambda _: settings.set("speed_limit", self._speed_box.currentData())
        )
        sl.addWidget(self._speed_box)
        sl.addWidget(hsep())

        # ── Proxy (#16) ──
        sl.addWidget(lbl("PROXY URL", 9, bold=True, color=P["muted"]))
        self._proxy_edit = QLineEdit(settings.get("proxy") or "")
        self._proxy_edit.setPlaceholderText("http://user:pass@host:port  (leave blank to disable)")
        self._proxy_edit.setMinimumHeight(36)
        self._proxy_edit.textChanged.connect(lambda v: settings.set("proxy", v.strip()))
        sl.addWidget(self._proxy_edit)
        sl.addWidget(hsep())

        # ── Cookies Browser (#15) ──
        sl.addWidget(lbl("COOKIES FROM BROWSER", 9, bold=True, color=P["muted"]))
        self._cookies_box = QComboBox()
        for label, val in [("None", ""), ("Chrome", "chrome"), ("Firefox", "firefox"), ("Edge", "edge")]:
            self._cookies_box.addItem(label, val)
        cur_browser = settings.get("cookies_browser") or ""
        for i in range(self._cookies_box.count()):
            if self._cookies_box.itemData(i) == cur_browser:
                self._cookies_box.setCurrentIndex(i)
                break
        self._cookies_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._cookies_box.currentIndexChanged.connect(
            lambda _: settings.set("cookies_browser", self._cookies_box.currentData())
        )
        sl.addWidget(self._cookies_box)
        sl.addWidget(hsep())

        # ── FFmpeg status ──
        ffmpeg_ok = shutil.which("ffmpeg") is not None
        status_msg = "FFmpeg ready. Merging and conversion are enabled." if ffmpeg_ok \
                 else "FFmpeg missing. MP3/merge may not work. Install from ffmpeg.org"
        sl.addWidget(lbl(status_msg, 9,
                         color=P["success"] if ffmpeg_ok else P["error"]))

        sl.addStretch()

        # ── Reset to Defaults ──
        reset_row = QHBoxLayout()
        reset_row.setContentsMargins(0, 4, 0, 0)
        self._reset_btn = btn("Reset to Defaults", P["error"], "#fff")
        self._reset_btn.setFixedHeight(36)
        self._reset_btn.clicked.connect(self._reset_settings)
        reset_row.addStretch()
        reset_row.addWidget(self._reset_btn)
        sl.addLayout(reset_row)

        # ── Version label ──
        ver = lbl(f"Alter v{APP_VERSION}", 8, color=P["muted"])
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(ver)

    @staticmethod
    def _theme_pill(active: bool) -> str:
        if active:
            return (f"QPushButton{{background:{P['accent']};color:#fff;"
                    f"border-radius:8px;border:none;padding:4px 14px;"
                    f"font-size:9pt;font-weight:600;}}")
        return (f"QPushButton{{background:{P['card']};color:{P['muted']};"
                f"border:1px solid {P['border']};border-radius:8px;"
                f"padding:4px 14px;font-size:9pt;}}"
                f"QPushButton:hover{{color:{P['text']};}}")

    def refresh_styles(self):
        """Re-apply inline styles after a theme change."""
        self._path_lbl.setStyleSheet(
            f"background:{P['card']};border:1px solid {P['border']};"
            f"border-radius:8px;padding:9px 14px;"
        )
        self._br_btn.setStyleSheet(f"""
            QPushButton {{
                background: {P['card_hover']}; color: {P['text']};
                border-radius: 8px; padding: 9px 20px;
                font-weight: 600; border: none;
            }}
            QPushButton:hover {{ background: {P['card_hover']}; }}
        """)
        current_theme = self._s.get("theme")
        for k, b in self._theme_btns.items():
            b.setStyleSheet(self._theme_pill(k == current_theme))
        current_notify = self._s.get("notify") or "each"
        for k, b in self._notify_btns.items():
            b.setStyleSheet(self._theme_pill(k == current_notify))

    def _set_theme(self, key: str):
        self._s.set("theme", key)
        for k, b in self._theme_btns.items():
            b.setChecked(k == key)
            b.setStyleSheet(self._theme_pill(k == key))
        self.sig_theme.emit(key)

    def _set_notify(self, key: str):
        self._s.set("notify", key)
        for k, b in self._notify_btns.items():
            b.setChecked(k == key)
            b.setStyleSheet(self._theme_pill(k == key))

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if d:
            self._s.set("save_path", d)
            self._path_lbl.setText(d)

    def _reset_settings(self):
        reply = QMessageBox.question(
            self,
            "Reset to Defaults",
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._s.reset()

        # Update all widgets to reflect the new defaults
        defaults = self._s.get_defaults()

        self._path_lbl.setText(defaults["save_path"])
        self._cc_box.setCurrentText(str(defaults["max_dl"]))
        self._tpl_edit.setText(defaults["filename_tpl"])
        self._proxy_edit.setText(defaults["proxy"])

        # Speed limit
        default_speed = int(defaults["speed_limit"])
        for i in range(self._speed_box.count()):
            if self._speed_box.itemData(i) == default_speed:
                self._speed_box.setCurrentIndex(i)
                break

        # Cookies browser
        default_browser = defaults["cookies_browser"]
        for i in range(self._cookies_box.count()):
            if self._cookies_box.itemData(i) == default_browser:
                self._cookies_box.setCurrentIndex(i)
                break

        # Theme buttons
        default_theme = defaults["theme"]
        for k, b in self._theme_btns.items():
            b.setChecked(k == default_theme)
            b.setStyleSheet(self._theme_pill(k == default_theme))
        self.sig_theme.emit(default_theme)

        # Notification buttons
        default_notify = defaults["notify"]
        for k, b in self._notify_btns.items():
            b.setChecked(k == default_notify)
            b.setStyleSheet(self._theme_pill(k == default_notify))
