from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QListWidgetItem, QDialogButtonBox
from PyQt6.QtCore import Qt

from ...theme import P
from ...utils.ui_helpers import lbl

class PlaylistDialog(QDialog):
    """Show playlist entries with checkboxes; return selected indices."""
    def __init__(self, entries: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Videos to Download")
        self.setMinimumSize(360, 400)
        self.setStyleSheet(f"background:{P['bg']};color:{P['text']};")

        lay = QVBoxLayout(self)
        lay.setSpacing(10)
        lay.setContentsMargins(16, 16, 16, 16)

        top = QHBoxLayout()
        top.addWidget(lbl(f"{len(entries)} videos in playlist", 10, bold=True))
        top.addStretch()
        sel_all = QPushButton("All")
        sel_none = QPushButton("None")
        for b in (sel_all, sel_none):
            b.setFixedHeight(32)
            b.setStyleSheet(f"QPushButton{{background:{P['card']};color:{P['muted']};"
                            f"border:1px solid {P['border']};border-radius:6px;"
                            f"padding:2px 10px;font-size:8pt;}}")
        sel_all.clicked.connect(lambda: [self._list.item(i).setCheckState(Qt.CheckState.Checked)
                                         for i in range(self._list.count())])
        sel_none.clicked.connect(lambda: [self._list.item(i).setCheckState(Qt.CheckState.Unchecked)
                                          for i in range(self._list.count())])
        top.addWidget(sel_all)
        top.addWidget(sel_none)
        lay.addLayout(top)

        self._list = QListWidget()
        self._list.setStyleSheet(f"QListWidget{{background:{P['surface']};border:none;"
                                  f"border-radius:8px;}}"
                                  f"QListWidget::item{{padding:6px 8px;color:{P['text']};}}"
                                  f"QListWidget::item:hover{{background:{P['card_hover']};}}")
        for e in entries:
            dur = e.get("duration", 0) or 0
            m, s = divmod(int(dur), 60)
            dur_s = f"  {m}:{s:02}" if dur else ""
            item = QListWidgetItem(f"{e['title'][:55]}{dur_s}")
            item.setCheckState(Qt.CheckState.Checked)
            self._list.addItem(item)
        lay.addWidget(self._list, 1)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        btns.setStyleSheet(f"QPushButton{{background:{P['accent']};color:#fff;"
                           f"border-radius:8px;padding:7px 18px;border:none;font-weight:600;}}"
                           f"QPushButton:hover{{background:{P['accent_h']};}}")
        lay.addWidget(btns)

    def selected_indices(self) -> list:
        return [i for i in range(self._list.count())
                if self._list.item(i).checkState() == Qt.CheckState.Checked]
