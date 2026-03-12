import shutil
from PyQt6.QtCore import QThread, pyqtSignal
import yt_dlp

from ..utils.errors import ANSI

class DownloadWorker(QThread):
    progress   = pyqtSignal(str, float, str, str)   # id, pct, speed, eta
    processing = pyqtSignal(str)                     # id
    done       = pyqtSignal(str, str, str, str)      # id, title, fmt, path
    failed     = pyqtSignal(str, str)                # id, error

    def __init__(self, dl_id, url, opts):
        super().__init__()
        self.id  = dl_id
        self.url = url
        self.opts = opts
        self._cancel = False

    def cancel(self): self._cancel = True

    def run(self):
        def hook(d):
            if self._cancel: raise Exception("Cancelled")
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                down  = d.get("downloaded_bytes", 0)
                pct   = (down / total * 100) if total else 0
                spd   = ANSI.sub("", d.get("_speed_str", "-") or "-").strip()
                eta   = ANSI.sub("", d.get("_eta_str",   "-") or "-").strip()
                self.progress.emit(self.id, pct, spd, eta)
            elif d["status"] == "finished":
                self.processing.emit(self.id)

        opts = {**self.opts, "progress_hooks": [hook], "quiet": True, "no_warnings": True}
        try:
            if not shutil.which("ffmpeg"):
                pass  # will warn earlier
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([self.url])
            self.done.emit(
                self.id,
                self.opts.get("_title", "Unknown"),
                self.opts.get("_fmt", "mp4"),
                self.opts.get("_path", "")
            )
        except Exception as e:
            if not self._cancel:
                self.failed.emit(self.id, str(e))
