import requests
from PyQt6.QtCore import QThread, pyqtSignal

from ..constants import APP_VERSION, GITHUB_RELEASES_URL

class UpdateChecker(QThread):
    update_available = pyqtSignal(str)  # emits latest version string

    def run(self):
        try:
            r = requests.get(GITHUB_RELEASES_URL, timeout=6,
                             headers={"Accept": "application/vnd.github+json"})
            if r.status_code == 200:
                tag = r.json().get("tag_name", "").lstrip("v")
                if tag and tag != APP_VERSION:
                    self.update_available.emit(tag)
        except:
            pass
