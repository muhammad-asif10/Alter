import datetime
import json

from ..constants import HISTORY_FILE

class HistoryManager:
    def __init__(self):
        self._data = []
        if HISTORY_FILE.exists():
            try: self._data = json.loads(HISTORY_FILE.read_text())
            except: pass

    def add(self, url, title, fmt, path):
        self._data.insert(0, {
            "url": url, "title": title, "format": fmt,
            "path": path, "date": datetime.datetime.now().isoformat()
        })
        self._data = self._data[:300]
        HISTORY_FILE.write_text(json.dumps(self._data, indent=2))

    def is_duplicate(self, url, fmt) -> bool:
        return any(e["url"] == url and e["format"] == fmt for e in self._data)

    def all(self):
        return list(self._data)

    def clear(self):
        self._data = []
        HISTORY_FILE.write_text("[]")
