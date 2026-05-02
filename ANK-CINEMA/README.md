# ANK-CINEMA v3.0: The One-Click Media Downloader

ANK-Cinema is a portable software suite designed to let you find and download movies and series instantly. Unlike other tools, it requires zero installation, zero technical configuration, and zero external software.

## Why use ANK-Cinema?

| Feature | ANK-Cinema v3.0 | Standard Tools |
| :--- | :--- | :--- |
| **Setup Time** | 10 Seconds | 10-20 Minutes |
| **Ease of Use** | Double-Click & Run | Requires Command Line |
| **Reliability** | Dual-Engine Search | Single Source (Fails often) |
| **Portability** | Run from a USB stick | Tied to your PC |

---

## Quick Start Guide

Choose the file for your computer and double-click to start.

| Your Computer | Run This File |
| :--- | :--- |
| **Windows** | **ANK-CINEMA.exe** (or .bat) |
| **macOS** | **ANK-CINEMA.command** |
| **Linux** | **ANK-CINEMA.desktop** |

---

## Three Steps to Your First Movie

1. **Launch**: Open the file listed above.
2. **Search**: Type the name of the movie or series (e.g., "The Batman").
3. **Download**: Pick your preferred quality (1080p, 4K, etc.) and let the app handle the rest.

---

## Advanced Features for Power Users

### Smart Self-Healing
If your Internet Service Provider (ISP) blocks torrent sites, ANK-Cinema will detect the block and offer to fix your DNS settings automatically. You don't need to know how networking works; the app handles it.

### Automatic Updates
You never have to visit GitHub again to get the latest version. The app checks for improvements every time you start it and can update itself in seconds.

### Professional Build Tool
If you are a developer, use the included **build.py** script to compile your own standalone version of the app for any system.

---

## Technical Details (For Developers)
- **Language**: Python 3.10+
- **Core Engine**: Bundled aria2c (Portable)
- **Scrapers**: Internal Pirate Bay API & TorrentGalaxy Scraper
- **Dependencies**: Managed automatically via local virtual environment

## License
Distributed under the MIT License.
