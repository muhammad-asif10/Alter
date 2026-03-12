import re

ANSI = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


def friendly_error_message(raw: str) -> str:
    """Map technical exceptions to actionable user-facing messages."""
    msg = (raw or "").lower()
    if any(k in msg for k in ("timed out", "timeout", "connection", "network")):
        return "Network timeout. Check your connection and retry."
    if any(k in msg for k in ("private", "unavailable", "not available", "removed")):
        return "This video is unavailable or private."
    if any(k in msg for k in ("ffmpeg", "postprocessing")):
        return "FFmpeg is required for this format. Install FFmpeg and retry."
    if any(k in msg for k in ("sign in", "login", "cookies", "age-restricted", "403", "forbidden")):
        return "This content may need sign-in. Try enabling browser cookies in Settings."
    if "proxy" in msg:
        return "Proxy failed. Check proxy settings and try again."
    return "Download failed. Please retry or try another format."

__all__ = ["ANSI", "friendly_error_message"]
