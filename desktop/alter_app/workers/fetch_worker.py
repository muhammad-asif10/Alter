from PyQt6.QtCore import QThread, pyqtSignal
import yt_dlp

class FetchWorker(QThread):
    done  = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
                info = ydl.extract_info(self.url, download=False)
            self.done.emit(info)
        except Exception as e:
            self.error.emit(str(e))
