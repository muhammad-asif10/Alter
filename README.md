<div align="center">

# Alter

**Download any video with one click.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/UI-PyQt6-green?logo=qt&logoColor=white)](https://pypi.org/project/PyQt6/)
[![yt-dlp](https://img.shields.io/badge/Engine-yt--dlp-red)](https://github.com/yt-dlp/yt-dlp)

</div>

---

## Overview

**Alter** is a fast, lightweight desktop video downloader powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp) and built with [PyQt6](https://pypi.org/project/PyQt6/). Paste any video URL, pick your format and quality, and download — no browser extensions, no command line required.

---

## Screenshots

<table>
  <tr>
    <td align="center"><strong>Home — Paste &amp; Preview</strong></td>
    <td align="center"><strong>Quality Selection</strong></td>
  </tr>
  <tr>
    <td><img src="https://github.com/user-attachments/assets/0a4903bd-7692-4369-b4af-01c1b8e0ecea" alt="Home screen showing URL input, video preview, format and quality selector" width="350"/></td>
    <td><img src="https://github.com/user-attachments/assets/ad77d9ad-5780-46c6-bd5d-ad47bfe6d3ae" alt="Quality selection with metadata, thumbnail and subtitle options" width="350"/></td>
  </tr>
  <tr>
    <td align="center"><strong>Downloads Queue</strong></td>
    <td align="center"><strong>History</strong></td>
  </tr>
  <tr>
    <td><img src="https://github.com/user-attachments/assets/bf0af629-78ca-49e3-aa6f-59822f25f8ce" alt="Downloads screen with active and queued items" width="350"/></td>
    <td><img src="https://github.com/user-attachments/assets/797d1188-e492-46ac-8a7e-cb4175b89b50" alt="History screen with searchable download log" width="350"/></td>
  </tr>
</table>

---

## Features

- 🔗 **One-click downloads** — paste a URL and hit the arrow button
- 🎞️ **Format selection** — choose Video (MP4), Audio-only, or Subtitle tracks
- 📐 **Quality picker** — select from all available resolutions with estimated file sizes
- 🖼️ **Optional extras** — download video metadata, embedded thumbnails, and subtitles
- 📥 **Download queue** — pause, resume, or clear the queue at any time
- 🕑 **History** — searchable log of every past download with timestamps
- 🌙 **Dark & light themes** — clean UI that adapts to your system
- 🪟 **Windows executable** — single `.exe` build via PyInstaller, no Python required to run

---

## Requirements

| Dependency | Version |
|---|---|
| Python | 3.10 or higher |
| PyQt6 | ≥ 6.4.0 |
| yt-dlp | ≥ 2024.1.1 |
| requests | ≥ 2.31.0 |
| Pillow | ≥ 10.0.0 |

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/muhammad-asif10/Alter.git
cd Alter
```

### 2. Create a virtual environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
python desktop/main.py
```

---

## How to Use

1. **Paste a URL** — copy any video link and paste it into the search bar on the **Home** tab, then press the **→** button.
2. **Preview** — the app fetches the video title, thumbnail, and available formats automatically.
3. **Choose format & quality** — select *Video (MP4)*, *Audio*, or *Subtitle* from the FORMAT section, then pick a resolution or bitrate from the QUALITY list.
4. **Optional extras** — tick **Metadata**, **Thumbnail**, or **Subtitles** if you need them embedded.
5. **Download** — confirm and the file is added to the queue on the **Downloads** tab.
6. **Manage downloads** — use **Pause Queue**, **Resume Queue**, or **Clear Queued** buttons as needed.
7. **View history** — switch to the **History** tab to search and review all past downloads.

---

## Build a Windows Executable

Use the included PyInstaller spec to produce a single, standalone `.exe`:

```bash
pip install pyinstaller
pyinstaller Alter.spec
```

The output executable is placed at:

```
dist/Alter.exe
```

> No Python installation is required on the target machine to run the built executable.

---

## Project Structure

```
Alter/
├── desktop/
│   ├── main.py            # Entry point
│   └── alter_app/         # Application package
├── img/                   # UI screenshots
├── requirements.txt       # Python dependencies
├── Alter.spec             # PyInstaller build spec
├── app_icon.ico           # Application icon
├── CONTRIBUTING.md        # Contribution guide
├── SECURITY.md            # Security policy
├── CODE_OF_CONDUCT.md     # Code of conduct
└── LICENSE                # MIT License
```

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

1. Fork the repository and create a feature branch from `main`.
2. Make focused, well-described commits.
3. Ensure the app starts without errors before submitting.
4. Include screenshots for any UI changes.

---

## Security

Please see [SECURITY.md](SECURITY.md) for responsible disclosure instructions.

---

## License

Released under the [MIT License](LICENSE). © 2026 Alter Contributors.
