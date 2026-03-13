from typing import Optional, Dict

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea, QFrame
from PyQt6.QtCore import Qt, pyqtSignal

from ...theme import P
from ...utils.ui_helpers import lbl, hsep
from ..widgets.download_card import DownloadCard

class DownloadsPage(QWidget):
    sig_pause_queue = pyqtSignal()
    sig_resume_queue = pyqtSignal()
    sig_clear_queued = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._cards: Dict[str, DownloadCard] = {}
        self._active_filter = "all"

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 14, 12, 10)
        root.setSpacing(9)

        hdr = QHBoxLayout()
        hdr.addWidget(lbl("Downloads", 14, bold=True))
        hdr.addStretch()
        self._lbl_count = lbl("0 items", 9, color=P["muted"])
        hdr.addWidget(self._lbl_count)
        root.addLayout(hdr)

        # ── Session summary + controls ──
        self._summary = lbl("Active 0  |  Queued 0  |  Failed 0  |  ETA -", 8, color=P["muted"])
        root.addWidget(self._summary)

        ctl = QHBoxLayout()
        ctl.setSpacing(6)
        self._b_pause = QPushButton("Pause Queue")
        self._b_resume = QPushButton("Resume Queue")
        self._b_clearq = QPushButton("Clear Queued")
        for b in (self._b_pause, self._b_resume, self._b_clearq):
            b.setFixedHeight(32)
            b.setStyleSheet(self._queue_btn_style())
        self._b_pause.clicked.connect(self.sig_pause_queue.emit)
        self._b_resume.clicked.connect(self.sig_resume_queue.emit)
        self._b_clearq.clicked.connect(self.sig_clear_queued.emit)
        ctl.addWidget(self._b_pause)
        ctl.addWidget(self._b_resume)
        ctl.addWidget(self._b_clearq)
        root.addLayout(ctl)

        # ── Filter pills ──
        filter_row = QHBoxLayout()
        filter_row.setSpacing(6)
        self._filter_btns: Dict[str, QPushButton] = {}
        for tag, label in [("all", "All"), ("mp4", "Video"),
                           ("mp3", "Audio"), ("srt", "Subtitle")]:
            b = QPushButton(label)
            b.setCheckable(True)
            b.setChecked(tag == "all")
            b.setFixedHeight(26)
            b.setStyleSheet(self._pill_style(tag == "all"))
            b.clicked.connect(lambda _, t=tag: self._set_filter(t))
            self._filter_btns[tag] = b
            filter_row.addWidget(b)
        filter_row.addStretch()
        root.addLayout(filter_row)
        root.addWidget(hsep())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._container = QWidget()
        self._vbox = QVBoxLayout(self._container)
        self._vbox.setSpacing(8)
        self._vbox.setContentsMargins(0, 4, 4, 4)

        # Empty state placeholder
        self._empty_lbl = lbl("No downloads yet.", 10, color=P["muted"])
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._vbox.addStretch()
        self._vbox.addWidget(self._empty_lbl)
        self._vbox.addStretch()

        scroll.setWidget(self._container)
        root.addWidget(scroll, 1)

    @staticmethod
    def _queue_btn_style() -> str:
        return (
            f"QPushButton{{background:{P['card_hover']};color:{P['text']};"
            f"border-radius:8px;border:none;padding:5px 10px;font-size:8pt;font-weight:600;}}"
            f"QPushButton:hover{{background:{P['border']};}}"
        )

    @staticmethod
    def _pill_style(active: bool) -> str:
        if active:
            return (f"QPushButton{{background:{P['accent']};color:#fff;"
                    f"border-radius:13px;border:none;padding:3px 12px;"
                    f"font-size:8pt;font-weight:600;}}")
        return (f"QPushButton{{background:{P['card']};color:{P['muted']};"
                f"border:1px solid {P['border']};border-radius:13px;"
                f"padding:3px 12px;font-size:8pt;}}"
                f"QPushButton:hover{{color:{P['text']};}}")

    def _set_filter(self, tag: str):
        self._active_filter = tag
        for t, b in self._filter_btns.items():
            b.setChecked(t == tag)
            b.setStyleSheet(self._pill_style(t == tag))
        self._apply_filter()

    def _apply_filter(self):
        for card in self._cards.values():
            if self._active_filter == "all":
                card.setVisible(True)
            else:
                card.setVisible(card._fmt == self._active_filter)

    def add(self, card: DownloadCard):
        self._cards[card.id] = card
        # Insert card before the bottom stretch (last item)
        self._vbox.insertWidget(self._vbox.count() - 1, card)
        self._empty_lbl.setVisible(False)
        self._apply_filter()
        self._refresh_count()

    def get(self, dl_id) -> Optional[DownloadCard]:
        return self._cards.get(dl_id)

    def _refresh_count(self):
        total  = len(self._cards)
        active = sum(1 for c in self._cards.values() if c.status in ("queued", "downloading", "processing"))
        self._lbl_count.setText(f"{active} active  ·  {total} total")

    def refresh_pill_styles(self):
        """Re-apply filter pill styles after a theme change (#4)."""
        for tag, b in self._filter_btns.items():
            b.setStyleSheet(self._pill_style(self._active_filter == tag))

    def refresh_styles(self):
        self._lbl_count.setStyleSheet(f"color: {P['muted']};")
        self._summary.setStyleSheet(f"color: {P['muted']};")
        self._empty_lbl.setStyleSheet(f"color: {P['muted']};")
        for b in (self._b_pause, self._b_resume, self._b_clearq):
            b.setStyleSheet(self._queue_btn_style())
        self.refresh_pill_styles()
        for c in self._cards.values():
            c.refresh_styles()

    def set_summary(self, active: int, queued: int, failed: int, eta_text: str = "-"):
        self._summary.setText(
            f"Active {active}  |  Queued {queued}  |  Failed {failed}  |  ETA {eta_text}"
        )
