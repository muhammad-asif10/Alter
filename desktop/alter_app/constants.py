import sys
import shutil
from pathlib import Path

APP_DIR = Path.home() / ".alter"
APP_DIR.mkdir(exist_ok=True)

# Migrate data from old ~/.goattube directory (#11)
_OLD_DIR = Path.home() / ".goattube"
if _OLD_DIR.exists():
    for _fname in ("history.json", "settings.json"):
        _src = _OLD_DIR / _fname
        _dst = APP_DIR / _fname
        if _src.exists() and not _dst.exists():
            shutil.copy2(_src, _dst)

HISTORY_FILE = APP_DIR / "history.json"
SETTINGS_FILE = APP_DIR / "settings.json"

APP_VERSION        = "1.0.0"
GITHUB_RELEASES_URL = "https://api.github.com/repos/your-org/alter/releases/latest"

# ── Mobile dimensions ────────────────────────────────────────────────────
MOBILE_W = 390
MOBILE_H = 650

ROOT_DIR = Path(__file__).resolve().parents[2]
APP_ICON_FILE = ROOT_DIR / "app_icon.ico"


def resolve_app_icon_path() -> Path:
    """Return icon path for source runs and PyInstaller bundled runs."""
    if hasattr(sys, "_MEIPASS"):
        bundled = Path(getattr(sys, "_MEIPASS")) / "app_icon.ico"
        if bundled.exists():
            return bundled
    return APP_ICON_FILE

__all__ = [
    "APP_DIR",
    "HISTORY_FILE",
    "SETTINGS_FILE",
    "APP_VERSION",
    "GITHUB_RELEASES_URL",
    "MOBILE_W",
    "MOBILE_H",
    "ROOT_DIR",
    "APP_ICON_FILE",
    "resolve_app_icon_path",
]
