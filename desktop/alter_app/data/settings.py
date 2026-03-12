import json
from pathlib import Path

from ..constants import SETTINGS_FILE

class Settings:
    _def = {
        "save_path":        str(Path.home() / "Downloads"),
        "max_dl":           3,
        "theme":            "dark",
        "filename_tpl":     "%(title)s.%(ext)s",
        "notify":           "each",     # each | batch | never
        "speed_limit":      0,          # 0 = unlimited, else KB/s
        "proxy":            "",
        "cookies_browser":  "",         # "" | chrome | firefox | edge
    }

    def __init__(self):
        self._d = dict(self._def)
        if SETTINGS_FILE.exists():
            try: self._d.update(json.loads(SETTINGS_FILE.read_text()))
            except: pass

    def get(self, k): return self._d.get(k, self._def.get(k))

    def set(self, k, v):
        self._d[k] = v
        SETTINGS_FILE.write_text(json.dumps(self._d, indent=2))
