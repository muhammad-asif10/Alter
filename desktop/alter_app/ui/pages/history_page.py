import datetime
import os
from pathlib import Path

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QScrollArea, QFrame, QSizePolicy, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal

from ...theme import P
from ...data.history import HistoryManager
from ...utils.ui_helpers import lbl, btn, hsep

class HistoryPage(QWidget):
    sig_redownload = pyqtSignal(str, dict, str, str)  # url, opts, title, fmt (#10)

    def __init__(self, history: HistoryManager):
        super().__init__()
        self._h = history

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 14, 12, 10)
        root.setSpacing(9)

        hdr = QHBoxLayout()
        hdr.addWidget(lbl("History", 14, bold=True))
        hdr.addStretch()
        clr_btn = btn("Clear", P["card_hover"], P["error"])
        clr_btn.setFixedWidth(70)
        clr_btn.clicked.connect(self._clear)
        hdr.addWidget(clr_btn)
        root.addLayout(hdr)

        # Search bar
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search history…")
        self._search.setMinimumHeight(36)
        self._search.textChanged.connect(self._apply_search)
        root.addWidget(self._search)

        root.addWidget(hsep())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._container = QWidget()
        self._vbox = QVBoxLayout(self._container)
        self._vbox.setSpacing(6)
        self._vbox.setContentsMargins(0, 4, 4, 4)
        scroll.setWidget(self._container)
        root.addWidget(scroll, 1)

        # ── Stats dashboard (#14) ──
        root.addWidget(hsep())
        self._stats_lbl = lbl("", 8, color=P["muted"])
        self._stats_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self._stats_lbl)

    def refresh_styles(self):
        self._stats_lbl.setStyleSheet(f"color: {P['muted']};")
        self.refresh()

    def refresh(self):
        while self._vbox.count():
            item = self._vbox.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        self._rows: list = []  # list of (widget, search_text)
        entries = self._h.all()

        # Update stats dashboard (#14)
        total = len(entries)
        week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
        this_week = sum(
            1 for e in entries
            if e.get("date") and datetime.datetime.fromisoformat(e["date"]) >= week_ago
        )
        self._stats_lbl.setText(
            f"Total: {total} download{'s' if total != 1 else ''}  ·  This week: {this_week}"
        )

        if not entries:
            ph = lbl("No downloads yet.", 10, color=P["muted"])
            ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._vbox.addWidget(ph)
            self._vbox.addStretch()
            return

        FMT_C = {"mp4": P["accent"], "mp3": P["purple"], "srt": P["cyan"]}
        for e in entries:
            row = QFrame()
            row.setObjectName("card")
            rl = QVBoxLayout(row)
            rl.setContentsMargins(12, 8, 12, 8)
            rl.setSpacing(3)

            top_r = QHBoxLayout()
            fmt = e.get("format", "mp4").split("-")[0]
            badge_bg = FMT_C.get(fmt.lower(), P["border"])
            badge = lbl(f" {fmt.upper()} ", 7, bold=True, color="#fff")
            badge.setStyleSheet(
                f"background:{badge_bg};color:white;"
                f"border-radius:4px;padding:1px 5px;font-weight:700;"
            )
            badge.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

            title_text = e.get("title", "?")[:45]
            title_lbl2 = lbl(title_text, 9, bold=True)
            title_lbl2.setWordWrap(False)

            try:
                dt = datetime.datetime.fromisoformat(e["date"])
                ds = dt.strftime("%b %d, %H:%M")
            except:
                ds = ""

            # Re-download button (#10)
            rdl_btn = QPushButton("↓")
            rdl_btn.setFixedSize(36, 36)
            rdl_btn.setToolTip("Re-download")
            rdl_btn.setStyleSheet(
                f"QPushButton{{background:{P['card_hover']};color:{P['accent']};"
                f"border-radius:6px;border:none;font-size:12pt;font-weight:700;}}"
                f"QPushButton:hover{{background:{P['accent']};color:#fff;}}"
            )
            entry_copy = dict(e)
            rdl_btn.clicked.connect(lambda _, ec=entry_copy: self._redownload(ec))

            top_r.addWidget(badge)
            top_r.addWidget(title_lbl2, 1)
            top_r.addWidget(rdl_btn)
            rl.addLayout(top_r)
            rl.addWidget(lbl(ds, 8, color=P["muted"]))
            self._vbox.addWidget(row)
            self._rows.append((row, title_text.lower()))

        self._vbox.addStretch()
        self._apply_search()

    def _redownload(self, entry: dict):
        url = entry.get("url", "")
        title = entry.get("title", "Unknown")
        fmt = entry.get("format", "mp4").split("-")[0]
        save = str(Path.home() / "Downloads")
        tpl = "%(title)s.%(ext)s"

        if fmt == "mp3":
            opts = {
                "format": "bestaudio/best",
                "outtmpl": os.path.join(save, tpl),
                "postprocessors": [
                    {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "320"},
                    {"key": "FFmpegMetadata", "add_metadata": True},
                ],
                "_title": title, "_fmt": "mp3", "_path": save,
            }
        elif fmt == "srt":
            opts = {
                "skip_download": True,
                "writesubtitles": True, "writeautomaticsub": True,
                "subtitleslangs": ["en"], "subtitlesformat": "srt",
                "outtmpl": os.path.join(save, tpl),
                "_title": title, "_fmt": "srt", "_path": save,
            }
        else:
            height = entry.get("format", "720p").replace("mp4-", "").replace("p", "")
            if not height.isdigit(): height = "720"
            opts = {
                "format": f"bestvideo[height<={height}]+bestaudio/best[height<={height}]",
                "outtmpl": os.path.join(save, tpl),
                "merge_output_format": "mp4",
                "_title": title, "_fmt": "mp4", "_path": save,
            }
        self.sig_redownload.emit(url, opts, title, fmt)

    def _apply_search(self):
        query = self._search.text().strip().lower()
        for widget, text in getattr(self, "_rows", []):
            widget.setVisible(not query or query in text)

    def _clear(self):
        r = QMessageBox.question(self, "Clear History", "Clear all download history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if r == QMessageBox.StandardButton.Yes:
            self._h.clear()
            self.refresh()
