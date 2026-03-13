import os
import re

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QPushButton, QLineEdit, QScrollArea, QSizePolicy, QLabel, QComboBox, QCheckBox, QApplication, QMessageBox, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal

from ...theme import P
from ...data.settings import Settings
from ...data.history import HistoryManager
from ...utils.ui_helpers import lbl, btn, hsep
from ...utils.errors import friendly_error_message
from ...workers.playlist_worker import PlaylistFetchWorker
from ...workers.fetch_worker import FetchWorker
from ...workers.thumb_loader import ThumbLoader
from ..widgets.playlist_dialog import PlaylistDialog

class SearchPage(QWidget):
    sig_download = pyqtSignal(str, dict, str, str, str)  # url,opts,title,fmt,thumb

    def __init__(self, settings: Settings, history: HistoryManager):
        super().__init__()
        self._s = settings
        self._h = history
        self._info = None
        self._fetch_worker = None
        self._playlist_worker = None

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 14, 12, 10)
        root.setSpacing(10)

        # Header
        hdr = QVBoxLayout()
        hdr.setSpacing(2)
        self._title_lbl = lbl("Alter", 17, bold=True, color=P["accent"])
        self._sub_lbl   = lbl("Download any video with one click", 8, color=P["muted"])
        hdr.addWidget(self._title_lbl)
        hdr.addWidget(self._sub_lbl)
        root.addLayout(hdr)

        root.addSpacing(8)

        # Update banner (hidden by default) (#18)
        self._update_banner = QFrame()
        self._update_banner.setObjectName("card")
        self._update_banner.setVisible(False)
        bn_lay = QHBoxLayout(self._update_banner)
        bn_lay.setContentsMargins(12, 8, 12, 8)
        self._update_lbl = lbl("", 8, color=P["warning"])
        bn_lay.addWidget(self._update_lbl)
        bn_lay.addStretch()
        self._bn_close = QPushButton("X")
        self._bn_close.setFixedSize(30, 30)
        self._bn_close.clicked.connect(lambda: self._update_banner.setVisible(False))
        bn_lay.addWidget(self._bn_close)
        root.addWidget(self._update_banner)

        # Clipboard prompt banner (hidden by default) (#6)
        self._clip_banner = QFrame()
        self._clip_banner.setObjectName("card")
        self._clip_banner.setVisible(False)
        cb_lay = QHBoxLayout(self._clip_banner)
        cb_lay.setContentsMargins(12, 8, 12, 8)
        self._clip_lbl = lbl("", 8, color=P["muted"])
        self._clip_lbl.setWordWrap(True)
        self._cb_use = QPushButton("Use")
        self._cb_use.setFixedHeight(32)
        self._cb_use.clicked.connect(self._use_clipboard)
        self._cb_dismiss = QPushButton("X")
        self._cb_dismiss.setFixedSize(30, 30)
        self._cb_dismiss.clicked.connect(lambda: self._clip_banner.setVisible(False))
        cb_lay.addWidget(self._clip_lbl, 1)
        cb_lay.addWidget(self._cb_use)
        cb_lay.addWidget(self._cb_dismiss)
        root.addWidget(self._clip_banner)
        self._last_clip = ""  # track to avoid re-prompting same URL

        # URL row — pill style
        url_row = QHBoxLayout()
        url_row.setSpacing(8)
        self._url = QLineEdit()
        self._url.setPlaceholderText("Paste the URL")
        self._url.setMinimumHeight(46)
        self._url.returnPressed.connect(self._fetch)

        self._btn_fetch = QPushButton("→")
        self._btn_fetch.setFixedSize(46, 46)
        self._apply_fetch_btn_style()
        self._btn_fetch.clicked.connect(self._fetch)

        url_row.addWidget(self._url, 1)
        url_row.addWidget(self._btn_fetch)
        root.addLayout(url_row)

        self._lbl_st = lbl("", 8, color=P["muted"])
        root.addWidget(self._lbl_st)

        # Preview (hidden until info loaded)
        self._preview_scroll = QScrollArea()
        self._preview_scroll.setWidgetResizable(True)
        self._preview_scroll.setVisible(False)
        self._preview_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._preview_inner = QWidget()
        self._preview_vbox  = QVBoxLayout(self._preview_inner)
        self._preview_vbox.setContentsMargins(0, 0, 4, 0)
        self._preview_scroll.setWidget(self._preview_inner)
        root.addWidget(self._preview_scroll, 1)

        self.refresh_styles()

    def _apply_fetch_btn_style(self):
        self._btn_fetch.setStyleSheet(f"""
            QPushButton {{
                background: {P['accent']}; color: white;
                border-radius: 23px; border: none;
                font-size: 16pt; font-weight: 700;
            }}
            QPushButton:hover {{ background: {P['accent_h']}; }}
            QPushButton:disabled {{
                background: {P['surface']};
                color: {P['muted']};
                border: 1px solid {P['border']};
            }}
        """)

    def refresh_styles(self):
        self._title_lbl.setStyleSheet(f"color: {P['accent']};")
        self._sub_lbl.setStyleSheet(f"color: {P['muted']};")
        self._update_lbl.setStyleSheet(f"color: {P['warning']};")
        self._clip_lbl.setStyleSheet(f"color: {P['muted']};")
        self._bn_close.setStyleSheet(f"background:transparent;color:{P['muted']};border:none;")
        self._cb_use.setStyleSheet(f"QPushButton{{background:{P['accent']};color:#fff;"
                                    f"border-radius:6px;border:none;padding:2px 10px;font-size:8pt;}}")
        self._cb_dismiss.setStyleSheet(f"background:transparent;color:{P['muted']};border:none;")
        self._lbl_st.setStyleSheet(f"color:{P['muted']};")
        self._apply_fetch_btn_style()

    def show_update_banner(self, version: str):
        self._update_lbl.setText(f"Update available: Alter v{version}. Visit GitHub to update.")
        self._update_banner.setVisible(True)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self._check_clipboard()

    def showEvent(self, event):
        super().showEvent(event)
        self._check_clipboard()

    def _check_clipboard(self):
        """Auto-detect video URL in clipboard (#6)."""
        clip = QApplication.clipboard().text().strip()
        if (clip != self._last_clip
                and re.match(r'^https?://', clip, re.IGNORECASE)
                and self._url.text().strip() == ""):
            self._last_clip = clip
            short = clip[:55] + ("…" if len(clip) > 55 else "")
            self._clip_lbl.setText(f"Detected URL in clipboard: {short}")
            self._clip_banner.setVisible(True)

    def _use_clipboard(self):
        self._url.setText(self._last_clip)
        self._clip_banner.setVisible(False)
        self._fetch()

    def _fetch(self):
        url = self._url.text().strip()
        if not url: return
        if not re.match(r'^https?://', url, re.IGNORECASE):
            self._lbl_st.setText("Please enter a valid URL starting with http:// or https://")
            self._lbl_st.setStyleSheet(f"color:{P['error']};")
            return

        # Cancel any in-flight fetch before starting a new one
        if self._fetch_worker and self._fetch_worker.isRunning():
            self._fetch_worker.done.disconnect()
            self._fetch_worker.error.disconnect()
            self._fetch_worker.quit()
            self._fetch_worker = None
        if self._playlist_worker and self._playlist_worker.isRunning():
            self._playlist_worker.done.disconnect()
            self._playlist_worker.error.disconnect()
            self._playlist_worker.quit()
            self._playlist_worker = None

        self._clear_preview()
        self._btn_fetch.setEnabled(False)
        self._btn_fetch.setText("…")

        # Detect playlist URLs (#5)
        is_playlist = ("list=" in url or "/playlist" in url or
                       re.search(r'[?&]list=', url))
        if is_playlist:
            self._lbl_st.setText("Fetching playlist…")
            self._lbl_st.setStyleSheet(f"color:{P['muted']};")
            self._playlist_worker = PlaylistFetchWorker(url)
            self._playlist_worker.done.connect(self._on_playlist)
            self._playlist_worker.error.connect(self._on_err)
            self._playlist_worker.start()
        else:
            self._lbl_st.setText("Fetching video information…")
            self._lbl_st.setStyleSheet(f"color:{P['muted']};")
            self._fetch_worker = FetchWorker(url)
            self._fetch_worker.done.connect(self._on_info)
            self._fetch_worker.error.connect(self._on_err)
            self._fetch_worker.start()

    def _on_playlist(self, entries: list):
        self._btn_fetch.setEnabled(True)
        self._btn_fetch.setText("→")
        if not entries:
            self._lbl_st.setText("No entries found in playlist.")
            self._lbl_st.setStyleSheet(f"color:{P['error']};")
            return
        self._lbl_st.setText("")
        dlg = PlaylistDialog(entries, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        indices = dlg.selected_indices()
        if not indices:
            return
        # Queue each selected entry as a single-video download
        for i in indices:
            e = entries[i]
            if e.get("url"):
                self._url.setText(e["url"])
                # Emit a fetch for each, but use a minimal opts dict
                save = self._s.get("save_path")
                tpl  = self._s.get("filename_tpl") or "%(title)s.%(ext)s"
                title = e.get("title", "Unknown")
                opts = {
                    "format": "bestvideo+bestaudio/best",
                    "outtmpl": os.path.join(save, tpl),
                    "merge_output_format": "mp4",
                    "_title": title, "_fmt": "mp4", "_path": save,
                }
                self.sig_download.emit(e["url"], opts, title, "mp4", "")

    def _on_err(self, msg):
        self._btn_fetch.setEnabled(True)
        self._btn_fetch.setText("→")
        self._lbl_st.setText(friendly_error_message(msg))
        self._lbl_st.setStyleSheet(f"color:{P['error']};")

    def _on_info(self, info):
        self._info = info
        self._btn_fetch.setEnabled(True)
        self._btn_fetch.setText("→")
        self._lbl_st.setText("")
        self._build_preview(info)

    def _clear_preview(self):
        self._info = None
        self._preview_scroll.setVisible(False)
        while self._preview_vbox.count():
            item = self._preview_vbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _build_preview(self, info):
        card = QFrame()
        card.setObjectName("card")
        cl = QVBoxLayout(card)
        cl.setSpacing(10)
        cl.setContentsMargins(12, 12, 12, 12)

        # ── Thumbnail (full width) ──
        thumb_url = info.get("thumbnail", "")
        thumb_lbl = QLabel()
        thumb_lbl.setFixedHeight(160)
        thumb_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb_lbl.setStyleSheet(
            f"background:{P['border']};border-radius:10px;"
            f"min-width:200px;"
        )
        thumb_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        if thumb_url:
            tl = ThumbLoader(thumb_url, 340, 160)
            tl.loaded.connect(thumb_lbl.setPixmap)
            tl.finished.connect(tl.deleteLater)
            thumb_lbl._tl = tl
            tl.start()
        cl.addWidget(thumb_lbl)

        # ── Meta ──
        title_lbl = lbl(info.get("title", "Unknown"), 10, bold=True)
        title_lbl.setWordWrap(True)

        dur = info.get("duration", 0)
        m, s = divmod(dur, 60); h, m = divmod(m, 60)
        dur_s = f"{h}:{m:02}:{s:02}" if h else f"{m}:{s:02}"
        uploader = info.get("uploader", "Unknown")
        views = f"{info.get('view_count', 0):,}"

        meta_lbl = lbl(f"{uploader}  ·  {dur_s}  ·  {views} views", 8, color=P["muted"])
        cl.addWidget(title_lbl)
        cl.addWidget(meta_lbl)
        cl.addWidget(hsep())

        # ── Format ──
        cl.addWidget(lbl("FORMAT", 8, bold=True, color=P["muted"]))
        fmt_box = QComboBox()
        fmt_box.addItems(["Video (MP4)", "Audio (MP3)", "Subtitles (SRT)"])
        fmt_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        cl.addWidget(fmt_box)

        # ── Video Quality ──
        res_lbl = lbl("QUALITY", 8, bold=True, color=P["muted"])
        res_box = QComboBox()
        res_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        cl.addWidget(res_lbl)
        cl.addWidget(res_box)

        resolutions = {}
        for f in info.get("formats", []):
            h = f.get("height")
            ext = f.get("ext")
            if h and ext in ("mp4", "webm"):
                size = f.get("filesize") or f.get("filesize_approx")
                if not size:
                    tbr = f.get("tbr")
                    if tbr and info.get("duration", 0):
                        size = (tbr * 1024 * info["duration"]) / 8
                key = f"{h}p"
                sz_str = f" (~{size/1024/1024:.1f} MB)" if size else ""
                if key not in resolutions or sz_str:
                    resolutions[key] = f"{h}p{sz_str}"

        sorted_res = sorted(resolutions.items(), key=lambda x: int(x[0][:-1]), reverse=True)
        for k, v in sorted_res:
            res_box.addItem(v, k)

        # ── Audio Quality (#7) ──
        aq_lbl = lbl("AUDIO QUALITY", 8, bold=True, color=P["muted"])
        aq_box = QComboBox()
        aq_box.addItem("High (320 kbps)", "320")
        aq_box.addItem("Medium (192 kbps)", "192")
        aq_box.addItem("Low (128 kbps)", "128")
        aq_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        aq_lbl.setVisible(False)
        aq_box.setVisible(False)
        cl.addWidget(aq_lbl)
        cl.addWidget(aq_box)

        # ── Subtitle Language (#8) ──
        sub_lbl = lbl("SUBTITLE LANGUAGE", 8, bold=True, color=P["muted"])
        sub_box = QComboBox()
        sub_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # Collect available subtitle languages from info
        all_subs = {}
        all_subs.update(info.get("subtitles", {}))
        all_subs.update(info.get("automatic_captions", {}))
        if all_subs:
            for lang_code in sorted(all_subs.keys()):
                sub_box.addItem(lang_code, lang_code)
            # Default to 'en' if available
            idx = sub_box.findData("en")
            if idx >= 0: sub_box.setCurrentIndex(idx)
        else:
            sub_box.addItem("en", "en")
        sub_lbl.setVisible(False)
        sub_box.setVisible(False)
        cl.addWidget(sub_lbl)
        cl.addWidget(sub_box)

        def on_fmt(idx):
            res_box.setVisible(idx == 0)
            res_lbl.setVisible(idx == 0)
            aq_lbl.setVisible(idx == 1)
            aq_box.setVisible(idx == 1)
            sub_lbl.setVisible(idx == 2)
            sub_box.setVisible(idx == 2)

        fmt_box.currentIndexChanged.connect(on_fmt)

        # ── Checkboxes ──
        chk_row = QHBoxLayout()
        chk_row.setSpacing(10)
        chk_meta  = QCheckBox("Metadata")
        chk_thumb = QCheckBox("Thumbnail")
        chk_subs  = QCheckBox("Subtitles")
        for c in (chk_meta, chk_thumb, chk_subs):
            c.setChecked(True)
            chk_row.addWidget(c)
        chk_row.addStretch()
        cl.addLayout(chk_row)

        # ── Download Button ──
        dl_btn = btn("↓   Download", P["accent"], hover=P["accent_h"])
        dl_btn.setMinimumHeight(44)
        dl_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        def do_download():
            url = self._url.text().strip()
            title = info.get("title", "Unknown")
            save = self._s.get("save_path")
            tpl  = self._s.get("filename_tpl") or "%(title)s.%(ext)s"
            fmt_idx = fmt_box.currentIndex()

            if fmt_idx == 0:  # Video
                res_key = res_box.currentData() or "720p"
                height  = res_key.replace("p", "")
                fmt_label = f"mp4-{height}p"
                if self._h.is_duplicate(url, fmt_label):
                    r = QMessageBox.question(self, "Duplicate",
                        f"'{title[:45]}' already downloaded at this quality.\nDownload again?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    if r == QMessageBox.StandardButton.No: return
                pp = []
                if chk_meta.isChecked():  pp.append({"key": "FFmpegMetadata", "add_metadata": True})
                if chk_thumb.isChecked(): pp.append({"key": "EmbedThumbnail"})
                opts = {
                    "format":  f"bestvideo[height<={height}]+bestaudio/best[height<={height}]",
                    "outtmpl": os.path.join(save, tpl),
                    "merge_output_format": "mp4",
                    "_title": title, "_fmt": "mp4", "_path": save,
                }
                if pp: opts["postprocessors"] = pp
                self.sig_download.emit(url, opts, title, "mp4", thumb_url)

            elif fmt_idx == 1:  # MP3
                quality = aq_box.currentData() or "320"
                if self._h.is_duplicate(url, "mp3"):
                    r = QMessageBox.question(self, "Duplicate",
                        f"'{title[:45]}' already downloaded as MP3.\nDownload again?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    if r == QMessageBox.StandardButton.No: return
                pp = [
                    {"key": "FFmpegExtractAudio", "preferredcodec": "mp3",
                     "preferredquality": quality},
                    {"key": "FFmpegMetadata", "add_metadata": True},
                ]
                if chk_thumb.isChecked(): pp.append({"key": "EmbedThumbnail"})
                opts = {
                    "format":  "bestaudio/best",
                    "outtmpl": os.path.join(save, tpl),
                    "postprocessors": pp,
                    "_title": title, "_fmt": "mp3", "_path": save,
                }
                self.sig_download.emit(url, opts, title, "mp3", thumb_url)

            else:  # Subtitles
                lang = sub_box.currentData() or "en"
                opts = {
                    "skip_download": True,
                    "writesubtitles": True, "writeautomaticsub": True,
                    "subtitleslangs": [lang], "subtitlesformat": "srt",
                    "outtmpl": os.path.join(save, tpl),
                    "_title": title, "_fmt": "srt", "_path": save,
                }
                self.sig_download.emit(url, opts, title, "srt", thumb_url)

        dl_btn.clicked.connect(do_download)
        cl.addWidget(dl_btn)

        self._preview_vbox.addWidget(card)
        self._preview_vbox.addStretch()
        self._preview_scroll.setVisible(True)
