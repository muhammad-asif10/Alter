import os
import sys
import uuid
from pathlib import Path
from typing import Dict

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QSystemTrayIcon, QMenu, QMessageBox, QStackedWidget
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QPalette, QShortcut, QKeySequence

from .constants import MOBILE_W, MOBILE_H, resolve_app_icon_path
from .theme import QSS, P, P_DARK, P_LIGHT, build_qss
from .utils.icons import SVG_SEARCH, SVG_DOWNLOAD, SVG_HISTORY, SVG_SETTINGS
from .data.history import HistoryManager
from .data.settings import Settings
from .workers.download_worker import DownloadWorker
from .workers.update_checker import UpdateChecker
from .ui.widgets.nav_btn import NavBtn
from .ui.widgets.download_card import DownloadCard
from .ui.pages.search_page import SearchPage
from .ui.pages.downloads_page import DownloadsPage
from .ui.pages.history_page import HistoryPage
from .ui.pages.settings_page import SettingsPage
from .utils.errors import friendly_error_message

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Alter")
        self.setFixedSize(MOBILE_W, MOBILE_H)
        self.setStyleSheet(QSS)

        self._history  = HistoryManager()
        self._settings = Settings()
        self._workers: Dict[str, DownloadWorker] = {}
        self._dl_queue: list = []   # pending (url, opts, title, fmt, thumb_url) tuples
        self._queued_cards: Dict[str, tuple] = {}  # dl_id → (url, opts, title, fmt, thumb)
        self._paused = False
        self._failed_count = 0

        # App icon
        icon_path = resolve_app_icon_path()
        icon = QIcon(str(icon_path)) if icon_path.exists() else self._make_app_icon()
        self.setWindowIcon(icon)

        # System tray
        self._tray = QSystemTrayIcon(icon, self)
        self._tray.setToolTip("Alter")
        tray_menu = QMenu()
        tray_menu.addAction("Open",  self.show)
        tray_menu.addAction("Quit",  QApplication.quit)
        self._tray.setContextMenu(tray_menu)
        self._tray.show()

        # Central layout
        central = QWidget()
        self.setCentralWidget(central)
        root_v = QVBoxLayout(central)
        root_v.setContentsMargins(0, 0, 0, 0)
        root_v.setSpacing(0)

        # Page stack
        self._stack = QStackedWidget()
        self._page_search    = SearchPage(self._settings, self._history)
        self._page_downloads = DownloadsPage()
        self._page_history   = HistoryPage(self._history)
        self._page_settings  = SettingsPage(self._settings)

        self._page_search.sig_download.connect(self._add_download)
        self._page_settings.sig_theme.connect(self._apply_theme)
        self._page_history.sig_redownload.connect(self._add_download)
        self._page_downloads.sig_pause_queue.connect(self._pause_queue)
        self._page_downloads.sig_resume_queue.connect(self._resume_queue)
        self._page_downloads.sig_clear_queued.connect(self._clear_queued)

        for p in (self._page_search, self._page_downloads,
                  self._page_history, self._page_settings):
            self._stack.addWidget(p)

        # Apply saved theme on startup (always, so QPalette is set correctly)
        saved_theme = self._settings.get("theme")
        self._apply_theme(saved_theme)

        # React to OS-level theme changes while the app is running (Qt 6.5+)
        try:
            QApplication.instance().styleHints().colorSchemeChanged.connect(
                self._on_system_color_scheme_changed
            )
        except AttributeError:
            pass

        root_v.addWidget(self._stack, 1)

        # Bottom tab bar
        bottom_bar = QFrame()
        bottom_bar.setObjectName("bottombar")
        bottom_bar.setFixedHeight(56)
        bb = QHBoxLayout(bottom_bar)
        bb.setContentsMargins(0, 0, 0, 0)
        bb.setSpacing(0)

        self._nav_btns = {}
        for key, svg, text in [
            ("search",    SVG_SEARCH,   "Home"),
            ("downloads", SVG_DOWNLOAD, "Downloads"),
            ("history",   SVG_HISTORY,  "History"),
            ("settings",  SVG_SETTINGS, "Setting"),
        ]:
            b = NavBtn(svg, text)
            b.clicked.connect(lambda _, k=key: self._nav(k))
            self._nav_btns[key] = b
            bb.addWidget(b)

        root_v.addWidget(bottom_bar)
        self._nav("search")

        # ── Keyboard shortcuts (#12) ──
        sc_focus = QShortcut(QKeySequence("Ctrl+L"), self)
        sc_focus.activated.connect(self._focus_url)

        sc_esc = QShortcut(QKeySequence("Escape"), self)
        sc_esc.activated.connect(self._handle_escape)

        sc_paste = QShortcut(QKeySequence("Ctrl+V"), self)
        sc_paste.activated.connect(self._focus_url_paste)

        # ── Start update checker (#18) ──
        self._update_checker = UpdateChecker()
        self._update_checker.update_available.connect(
            self._page_search.show_update_banner
        )
        self._update_checker.start()
        self._refresh_download_summary()

    # ── Keyboard shortcut handlers ──
    def _focus_url(self):
        self._nav("search")
        self._page_search._url.setFocus()
        self._page_search._url.selectAll()

    def _focus_url_paste(self):
        self._nav("search")
        self._page_search._url.setFocus()
        # QShortcut fires before default paste, so just focus and let OS paste
        QTimer.singleShot(0, lambda: self._page_search._url.paste())

    def _handle_escape(self):
        if self._stack.currentIndex() == 0:
            # Clear URL field and hide preview on search page
            self._page_search._url.clear()
            self._page_search._preview_scroll.setVisible(False)
            while self._page_search._preview_vbox.count():
                item = self._page_search._preview_vbox.takeAt(0)
                if item.widget(): item.widget().deleteLater()

    def _pause_queue(self):
        self._paused = True
        self._notify_message(
            "Queue Paused", "New queued items will wait until resume.",
            QSystemTrayIcon.MessageIcon.Information, 1800
        )
        self._refresh_download_summary()

    def _notify_message(self, title: str, message: str,
                        icon: QSystemTrayIcon.MessageIcon,
                        timeout_ms: int = 3500):
        """Show desktop notification with fallback when tray messages are unavailable."""
        try:
            if (QSystemTrayIcon.isSystemTrayAvailable()
                    and self._tray.supportsMessages()):
                self._tray.showMessage(title, message, icon, timeout_ms)
                return
        except Exception:
            pass

        # Fallback: non-blocking dialog so user still sees completion/failure events.
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(message)
        if icon == QSystemTrayIcon.MessageIcon.Warning:
            box.setIcon(QMessageBox.Icon.Warning)
        else:
            box.setIcon(QMessageBox.Icon.Information)
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        box.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        box.show()
        QTimer.singleShot(min(timeout_ms, 5000), box.close)

    def _resume_queue(self):
        self._paused = False
        self._drain_queue()
        self._refresh_download_summary()

    def _clear_queued(self):
        self._dl_queue.clear()
        for dl_id in list(self._queued_cards.keys()):
            card = self._page_downloads.get(dl_id)
            if card:
                card.setVisible(False)
        self._queued_cards.clear()
        self._refresh_download_summary()

    def _refresh_download_summary(self):
        eta_text = "-"
        for card in getattr(self._page_downloads, "_cards", {}).values():
            if card.status == "downloading" and "ETA" in card._lbl_speed.text():
                eta_text = card._lbl_speed.text().split("ETA", 1)[-1].strip() or "-"
                break
        self._page_downloads.set_summary(
            active=len(self._workers),
            queued=len(self._dl_queue),
            failed=self._failed_count,
            eta_text=eta_text,
        )

    # ── App Icon ──
    @staticmethod
    def _make_app_icon(size: int = 64) -> QIcon:
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor("#1B2B4B"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, size, size)
        painter.setPen(QColor("#FFFFFF"))
        font = QFont("Segoe UI", int(size * 0.30), QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "At")
        painter.end()
        return QIcon(pix)

    # ── Theme ──
    @staticmethod
    def _system_is_light_now() -> bool:
        app = QApplication.instance()
        if app is None:
            return False
        try:
            scheme = app.styleHints().colorScheme()
            if scheme == Qt.ColorScheme.Light:
                return True
            if scheme == Qt.ColorScheme.Dark:
                return False
        except Exception:
            pass

        # Windows fallback: read OS app theme preference directly.
        if sys.platform == "win32":
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                )
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                winreg.CloseKey(key)
                return bool(value)
            except Exception:
                pass

        return app.palette().color(QPalette.ColorRole.Window).lightness() > 128

    def _apply_theme(self, name: str):
        if name == "system":
            palette = P_LIGHT if self._system_is_light_now() else P_DARK
        elif name == "light":
            palette = P_LIGHT
        else:
            palette = P_DARK
        P.update(palette)
        new_qss = build_qss(P)

        app = QApplication.instance()
        app.setStyleSheet(new_qss)

        # Keep QPalette in sync so Qt-native rendering uses the correct colours
        qpal = QPalette()
        qpal.setColor(QPalette.ColorRole.Window,          QColor(P["bg"]))
        qpal.setColor(QPalette.ColorRole.WindowText,      QColor(P["text"]))
        qpal.setColor(QPalette.ColorRole.Base,            QColor(P["card"]))
        qpal.setColor(QPalette.ColorRole.AlternateBase,   QColor(P["surface"]))
        qpal.setColor(QPalette.ColorRole.Text,            QColor(P["text"]))
        qpal.setColor(QPalette.ColorRole.Button,          QColor(P["card"]))
        qpal.setColor(QPalette.ColorRole.ButtonText,      QColor(P["text"]))
        qpal.setColor(QPalette.ColorRole.Highlight,       QColor(P["accent"]))
        qpal.setColor(QPalette.ColorRole.HighlightedText, QColor("#fff"))
        app.setPalette(qpal)

        self.setStyleSheet(new_qss)

        for k, b in getattr(self, "_nav_btns", {}).items():
            is_checked = b.isChecked()
            b._apply_color(P["accent"] if is_checked else P["muted"])

        if hasattr(self, "_page_settings"):
            self._page_settings.refresh_styles()

        if hasattr(self, "_page_search"):
            self._page_search.refresh_styles()

        if hasattr(self, "_page_history"):
            self._page_history.refresh_styles()

        if hasattr(self, "_page_downloads"):
            self._page_downloads.refresh_styles()

    def _on_system_color_scheme_changed(self, *_):
        """Called when the OS switches between light and dark mode (Qt 6.5+)."""
        if self._settings.get("theme") == "system":
            self._apply_theme("system")

    # ── Navigation ──
    def _nav(self, key):
        pages = {"search": 0, "downloads": 1, "history": 2, "settings": 3}
        self._stack.setCurrentIndex(pages[key])
        for k, b in self._nav_btns.items():
            b.setChecked(k == key)
        if key == "history":
            self._page_history.refresh()

    # ── Queue position helper ──
    def _update_queue_positions(self):
        for i, (url, opts, title, fmt, thumb_url) in enumerate(self._dl_queue):
            # Find the matching queued card by title+fmt (best effort)
            for dl_id, info in self._queued_cards.items():
                if info[2] == title and info[3] == fmt:
                    card = self._page_downloads.get(dl_id)
                    if card: card.set_queue_position(i + 1)
                    break

    # ── Download orchestration ──
    def _add_download(self, url, opts, title, fmt, thumb_url=""):
        # Check if already actively downloading
        for w in self._workers.values():
            if w.url == url and w.opts.get("_fmt") == fmt:
                QMessageBox.information(self, "Already Downloading",
                    f"'{title[:45]}' is already being downloaded.")
                return

        max_dl = int(self._settings.get("max_dl"))
        if len(self._workers) >= max_dl:
            dl_id = uuid.uuid4().hex[:8]
            card = DownloadCard(dl_id, title, fmt, thumb_url, url=url, opts=opts)
            card.sig_cancel.connect(self._cancel)
            card.sig_open.connect(self._open_folder)
            card.sig_retry.connect(self._retry)
            self._page_downloads.add(card)
            self._dl_queue.append((url, opts, title, fmt, thumb_url))
            self._queued_cards[dl_id] = (url, opts, title, fmt, thumb_url)
            self._update_queue_positions()
            self._refresh_download_summary()
            self._nav("downloads")
            return

        if self._paused:
            dl_id = uuid.uuid4().hex[:8]
            card = DownloadCard(dl_id, title, fmt, thumb_url, url=url, opts=opts)
            card.sig_cancel.connect(self._cancel)
            card.sig_open.connect(self._open_folder)
            card.sig_retry.connect(self._retry)
            self._page_downloads.add(card)
            self._dl_queue.append((url, opts, title, fmt, thumb_url))
            self._queued_cards[dl_id] = (url, opts, title, fmt, thumb_url)
            self._update_queue_positions()
            self._refresh_download_summary()
            self._nav("downloads")
            return

        self._start_worker(url, opts, title, fmt, thumb_url)
        self._refresh_download_summary()
        self._nav("downloads")

    def _start_worker(self, url, opts, title, fmt, thumb_url=""):
        dl_id = uuid.uuid4().hex[:8]

        # Apply settings: speed limit, proxy, cookies
        opts = dict(opts)  # don't mutate caller's dict
        speed = int(self._settings.get("speed_limit") or 0)
        if speed > 0:
            opts["ratelimit"] = speed * 1024

        proxy = self._settings.get("proxy") or ""
        if proxy:
            opts["proxy"] = proxy

        browser = self._settings.get("cookies_browser") or ""
        if browser:
            opts["cookiesfrombrowser"] = (browser, None, None, None)

        card = DownloadCard(dl_id, title, fmt, thumb_url, url=url, opts=opts)
        card.sig_cancel.connect(self._cancel)
        card.sig_open.connect(self._open_folder)
        card.sig_retry.connect(self._retry)
        self._page_downloads.add(card)

        worker = DownloadWorker(dl_id, url, opts)
        worker.progress.connect(lambda i, p, s, e:
            self._page_downloads.get(i) and
            self._page_downloads.get(i).on_progress(p, s, e))
        worker.processing.connect(lambda i:
            self._page_downloads.get(i) and
            self._page_downloads.get(i).on_processing())
        worker.done.connect(self._on_done)
        worker.failed.connect(self._on_fail)
        worker.start()

        self._workers[dl_id] = worker
        self._refresh_download_summary()

    def _drain_queue(self):
        if self._paused:
            self._refresh_download_summary()
            return
        max_dl = int(self._settings.get("max_dl"))
        while self._dl_queue and len(self._workers) < max_dl:
            url, opts, title, fmt, thumb_url = self._dl_queue.pop(0)
            # Remove this entry from queued_cards
            for dl_id, info in list(self._queued_cards.items()):
                if info[2] == title and info[3] == fmt:
                    self._queued_cards.pop(dl_id, None)
                    # Remove the queued card from downloads page
                    card = self._page_downloads.get(dl_id)
                    if card: card.setVisible(False)
                    break
            self._start_worker(url, opts, title, fmt, thumb_url)
        self._update_queue_positions()
        self._refresh_download_summary()

    def _retry(self, dl_id: str):
        card = self._page_downloads.get(dl_id)
        if not card or not card.url:
            return
        url  = card.url
        opts = dict(card.opts or {})
        title = opts.get("_title", "Unknown")
        fmt   = opts.get("_fmt", "mp4")
        thumb = ""
        # Hide failed card so retry creates a single clear active attempt.
        card.setVisible(False)
        self._start_worker(url, opts, title, fmt, thumb)
        self._refresh_download_summary()

    def _on_done(self, dl_id, title, fmt, path):
        card = self._page_downloads.get(dl_id)
        if card: card.on_done(path)

        url = self._workers[dl_id].url if dl_id in self._workers else ""
        self._history.add(url, title, fmt, path)

        notify = self._settings.get("notify") or "each"
        if notify == "each":
            self._notify_message(
                "Download Complete", f"  {title[:55]}",
                QSystemTrayIcon.MessageIcon.Information, 3500
            )
        elif notify == "batch":
            self._workers.pop(dl_id, None)
            self._drain_queue()
            # Show summary only when queue is fully drained
            if not self._workers and not self._dl_queue:
                self._notify_message(
                    "All Downloads Complete",
                    "Your downloads have finished.",
                    QSystemTrayIcon.MessageIcon.Information, 3500
                )
            self._refresh_download_summary()
            return
        # "never" → no tray message

        self._workers.pop(dl_id, None)
        self._drain_queue()
        self._refresh_download_summary()

    def _on_fail(self, dl_id, msg):
        card = self._page_downloads.get(dl_id)
        if card: card.on_error(msg)
        self._failed_count += 1
        notify = self._settings.get("notify") or "each"
        if notify != "never":
            self._notify_message(
                "Download Failed", friendly_error_message(msg),
                QSystemTrayIcon.MessageIcon.Warning, 4000
            )
        self._workers.pop(dl_id, None)
        self._drain_queue()
        self._refresh_download_summary()

    def _cancel(self, dl_id):
        # Cancel active worker
        if dl_id in self._workers:
            self._workers[dl_id].cancel()
            self._workers.pop(dl_id)
        # Remove from queue if it was queued
        elif dl_id in self._queued_cards:
            info = self._queued_cards.pop(dl_id)
            # Remove from _dl_queue by matching url+fmt
            self._dl_queue = [
                item for item in self._dl_queue
                if not (item[0] == info[0] and item[3] == info[3] and item[2] == info[2])
            ]
            self._update_queue_positions()
        card = self._page_downloads.get(dl_id)
        if card: card.setVisible(False)
        self._refresh_download_summary()

    def _open_folder(self, path):
        folder = path if os.path.isdir(path) else str(Path(path).parent)
        if sys.platform == "win32":
            os.startfile(folder)
        elif sys.platform == "darwin":
            import subprocess; subprocess.run(["open", folder])
        else:
            import subprocess; subprocess.run(["xdg-open", folder])

    def closeEvent(self, event):
        if self._workers:
            r = QMessageBox.question(self, "Downloads Active",
                f"{len(self._workers)} download(s) still running.\nQuit anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if r == QMessageBox.StandardButton.No:
                event.ignore(); return

        for dl_id, w in list(self._workers.items()):
            title = w.opts.get("_title", "Unknown")
            fmt   = w.opts.get("_fmt", "mp4")
            self._history.add(w.url, f"[interrupted] {title}", fmt, "")

        for w in self._workers.values():
            w.cancel()
        for w in self._workers.values():
            w.wait(3000)

        event.accept()
