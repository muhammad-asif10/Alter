import requests
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage

class ThumbLoader(QThread):
    loaded = pyqtSignal(QPixmap)

    def __init__(self, url, w, h):
        super().__init__()
        self.url, self.tw, self.th = url, w, h

    def run(self):
        try:
            r = requests.get(self.url, timeout=6)
            qimg = QImage.fromData(r.content)
            if qimg.isNull():
                return
            pix = QPixmap.fromImage(qimg).scaled(
                self.tw, self.th,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            cx = (pix.width() - self.tw) // 2
            cy = (pix.height() - self.th) // 2
            self.loaded.emit(pix.copy(cx, cy, self.tw, self.th))
        except:
            pass
