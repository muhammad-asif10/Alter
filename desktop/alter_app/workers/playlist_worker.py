from PyQt6.QtCore import QThread, pyqtSignal
import yt_dlp

class PlaylistFetchWorker(QThread):
    done  = pyqtSignal(list)   # list of {title, url, duration} dicts
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            opts = {
                "quiet": True, "no_warnings": True,
                "extract_flat": True, "skip_download": True,
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
            entries = info.get("entries") or []
            result = []
            for e in entries:
                if e:
                    result.append({
                        "title": e.get("title", "Unknown"),
                        "url": e.get("url") or e.get("webpage_url", ""),
                        "duration": e.get("duration", 0),
                    })
            self.done.emit(result)
        except Exception as ex:
            self.error.emit(str(ex))
