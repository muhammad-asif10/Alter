from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QSizePolicy, QPushButton, QLabel, QProgressBar
from PyQt6.QtCore import Qt, pyqtSignal

from ...theme import P
from ...utils.ui_helpers import lbl
from ...utils.errors import friendly_error_message

class DownloadCard(QFrame):
    sig_cancel = pyqtSignal(str)
    sig_open   = pyqtSignal(str)
    sig_retry  = pyqtSignal(str)  # emits dl_id (#1/#3)

    FMT_COLOR = {"mp4": P["accent"], "mp3": P["purple"], "srt": P["cyan"]}
    STATE_COLOR = {
        "queued": P["muted"],
        "downloading": P["accent"],
        "processing": P["warning"],
        "done": P["success"],
        "error": P["error"],
    }

    def __init__(self, dl_id, title, fmt, thumb_url="", url="", opts=None):
        super().__init__()
        self.setObjectName("card")
        self.id = dl_id
        self.status = "queued"
        self._save_path = ""
        self._fmt = fmt.lower()
        self.url  = url               # stored for retry (#3)
        self.opts = opts or {}        # stored for retry (#3)

        self.setMinimumHeight(78)
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(5)

        # ── Top row: badge + title + cancel btn ──
        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        badge_bg = self.FMT_COLOR.get(fmt.lower(), P["border"])
        self._badge = lbl(f" {fmt.upper()} ", 7, bold=True, color="#fff")
        self._badge.setStyleSheet(
            f"background:{badge_bg};color:white;"
            f"border-radius:4px;padding:2px 5px;font-size:7pt;font-weight:700;"
        )
        self._badge.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self._lbl_title = lbl(
            (title[:30] + "…") if len(title) > 30 else title,
            9, bold=True
        )
        self._lbl_title.setWordWrap(False)

        self._btn_x = QPushButton("X")
        self._btn_x.setFixedSize(28, 28)
        self._btn_x.setStyleSheet(
            f"background:{P['card_hover']};color:{P['muted']};"
            f"border-radius:8px;border:none;font-size:8px;font-weight:700;"
        )
        self._btn_x.clicked.connect(lambda: self.sig_cancel.emit(self.id))

        self._btn_open = QPushButton("Open")
        self._btn_open.setFixedSize(44, 28)
        self._btn_open.setStyleSheet(
            f"background:{P['card_hover']};color:{P['muted']};"
            f"border-radius:8px;border:none;font-size:8px;font-weight:700;"
        )
        self._btn_open.setVisible(False)
        self._btn_open.clicked.connect(lambda: self.sig_open.emit(self._save_path))

        self._btn_retry = QPushButton("Retry")
        self._btn_retry.setFixedSize(48, 28)
        self._btn_retry.setStyleSheet(
            f"background:{P['warning']};color:#fff;"
            f"border-radius:8px;border:none;font-size:8px;font-weight:700;"
        )
        self._btn_retry.setVisible(False)
        self._btn_retry.setToolTip("Retry download")
        self._btn_retry.clicked.connect(lambda: self.sig_retry.emit(self.id))

        top_row.addWidget(self._badge)

        self._state_pill = QLabel("Queued")
        self._state_pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._state_pill.setMinimumWidth(64)
        self._state_pill.setStyleSheet("")
        self._apply_state_pill("queued")
        top_row.addWidget(self._state_pill)

        top_row.addWidget(self._lbl_title, 1)
        top_row.addWidget(self._btn_retry)
        top_row.addWidget(self._btn_x)
        top_row.addWidget(self._btn_open)
        root.addLayout(top_row)

        # ── Progress bar ──
        self._bar = QProgressBar()
        self._bar.setMaximum(100)
        self._bar.setValue(0)
        self._bar.setFixedHeight(3)
        self._bar.setTextVisible(False)
        root.addWidget(self._bar)

        # ── Status row ──
        info_row = QHBoxLayout()
        self._lbl_status = lbl("Queued", 8, color=P["muted"])
        self._lbl_speed  = lbl("", 8, color=P["muted"])
        info_row.addWidget(self._lbl_status)
        info_row.addStretch()
        info_row.addWidget(self._lbl_speed)
        root.addLayout(info_row)

    def set_queue_position(self, pos: int):
        """Show queue position on card (#2)."""
        self._apply_state_pill("queued")
        if pos > 0:
            self._lbl_status.setText(f"Queued #{pos}")
            self._lbl_status.setStyleSheet(f"color:{P['muted']};")
        else:
            self._lbl_status.setText("Queued")
            self._lbl_status.setStyleSheet(f"color:{P['muted']};")

    def _apply_state_pill(self, state: str):
        color = self.STATE_COLOR.get(state, P["muted"])
        txt = {
            "queued": "Queued",
            "downloading": "Running",
            "processing": "Processing",
            "done": "Done",
            "error": "Failed",
        }.get(state, state.title())
        self._state_pill.setText(txt)
        self._state_pill.setStyleSheet(
            f"background:{color};color:#fff;border-radius:6px;"
            f"padding:2px 7px;font-size:7pt;font-weight:700;"
        )

    def on_progress(self, pct, spd, eta):
        self.status = "downloading"
        self._apply_state_pill("downloading")
        self._bar.setValue(int(pct))
        self._lbl_status.setText(f"{pct:.1f}%")
        self._lbl_status.setStyleSheet(f"color:{P['accent']};")
        cleaned = (f"{spd}   ETA {eta}").replace("Unknown", "").strip()
        self._lbl_speed.setText(cleaned)

    def on_processing(self):
        self.status = "processing"
        self._apply_state_pill("processing")
        self._bar.setValue(99)
        self._lbl_status.setText("Processing…")
        self._lbl_status.setStyleSheet(f"color:{P['warning']};")
        self._lbl_speed.setText("")

    def on_done(self, path):
        self.status = "done"
        self._apply_state_pill("done")
        self._save_path = path
        self._bar.setValue(100)
        self._bar.setStyleSheet(
            f"QProgressBar::chunk{{background:{P['success']};border-radius:3px;}}"
        )
        self._lbl_status.setText("Done")
        self._lbl_status.setStyleSheet(f"color:{P['success']};")
        self._lbl_speed.setText("")
        self._btn_x.setVisible(False)
        self._btn_open.setVisible(True)

    def on_error(self, msg):
        self.status = "error"
        self._apply_state_pill("error")
        self._bar.setStyleSheet(
            f"QProgressBar::chunk{{background:{P['error']};border-radius:3px;}}"
        )
        clean = friendly_error_message(msg)
        self._lbl_status.setText(f"Error: {clean[:42]}")
        self._lbl_status.setStyleSheet(f"color:{P['error']};")
        self._btn_x.setVisible(False)
        self._btn_retry.setVisible(True)  # show retry on failure (#1)
