# 🎬 ANK-CINEMA v3.0: Portable Media Suite

ANK-Cinema is a professional-grade, standalone media downloader designed for speed, privacy, and absolute ease of use. It transforms the complex process of finding and acquiring movies and series into a simple, one-click experience.

---

### 🌟 Key Features

- ✅ **Internal Search Engine**: Queries multiple sources (TPB, TorrentGalaxy) in parallel without external tools.
- ✅ **Zero-Configuration**: Fully portable. All settings and binaries stay inside the project folder.
- ✅ **Smart Diagnostics**: Automatically detects and repairs ISP blocks or DNS issues.
- ✅ **High-Speed Core**: Bundles a pre-configured aria2c engine for maximum download velocity.
- ✅ **Auto-Updating**: Stay current with the latest scrapers via the built-in update system.

---

### 🚀 Quick Start (One-Click)

No installation or command-line knowledge is required. Just run the file for your system:

| System | Action | File to Run |
| :--- | :--- | :--- |
| **Windows** | Double-click | `ANK-CINEMA.exe` (or .bat) |
| **macOS** | Double-click | `ANK-CINEMA.command` |
| **Linux** | Run | `ANK-CINEMA.desktop` |

---

### 📦 How it Works

1. **First Launch**: The app builds a private environment (`.venv`) and prepares the high-speed engine (`bin/`).
2. **Search**: Enter the name of any movie or series. The app checks spelling and offers corrections.
3. **Download**: Select your preferred quality. The app manages the metadata and starts the download immediately.

---

### ⚙️ Customization

Settings are managed via `config/config.json`. You can customize:
- **Download Path**: Set your preferred movie folder.
- **Max Results**: Control how many search hits you see.
- **Real-Debrid**: Add your API key for premium cached downloads.

---

### 🛡️ Long-Term Support (LTS)

ANK-Cinema is designed for stability. If a search source goes down, the app automatically switches to a fallback engine. If a technical issue occurs, a detailed report is saved to `logs/error.log` for easy troubleshooting.

---

### 🛠️ Developer Tools

Use `build.py` to compile the script into a standalone binary for distribution.
```bash
python build.py
```
*Results will be available in the `dist/` folder.*

---

## License
Distributed under the MIT License. Created by [Aizaz-Noor](https://github.com/Aizaz-Noor).
