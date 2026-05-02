# ANK-CINEMA v3.0

ANK-Cinema is a standalone, cross-platform media downloader. It provides a one-click interface for searching and acquiring movies and series using a parallel, multi-source search engine. Version 3.0 is built as an autonomous "Black Box" that requires no external installation or technical configuration.

## Tutorial: Getting Started

### Windows
1. Download the repository folder.
2. Double-click ANK-CINEMA.bat.
3. The launcher will automatically configure a private environment and start the app.

### macOS and Linux
1. Download the repository folder.
2. Run ANK-CINEMA.command (macOS) or ANK-CINEMA.desktop (Linux).
3. The system will handle dependency installation and launch the core.

## How-To Guides

### Changing the Download Directory
All settings are stored in config/config.json. To change where movies are saved:
1. Open config/config.json in a text editor.
2. Modify the "target_dir" path.
3. Save and restart the app.

### Troubleshooting Network Blocks
If your ISP blocks torrent metadata, the app will detect this during launch.
- On Linux, the app can automatically switch to Google or Cloudflare DNS.
- On Windows, ensure your DNS is set to 8.8.8.8 or use a VPN.
- Check logs/error.log for specific connection failure details.

## Technical Reference

### File Structure
- ank_cinema_core.py: The main application logic and search engine.
- bin/: Contains the bundled aria2c engine.
- config/: Stores user settings and search history.
- logs/: Contains error logs for troubleshooting.
- build.py: Tool for compiling the script into a standalone .exe or binary.

### Dependencies
The app manages its own dependencies. It requires Python 3.10 or higher. On first run, it installs:
- requests: For API and web scraping.
- rich: For the terminal user interface.
- aria2c: The high-speed download engine (auto-downloaded).

## Explanation: Why v3.0?

Previous versions relied on external tools like pirate-get, which required manual installation and often broke due to dependency conflicts. Version 3.0 uses an internal scraping logic that queries multiple torrent databases in parallel. This makes the software portable, faster, and immune to system-wide library changes.

## Building from Source

To create your own standalone executable:
1. Open a terminal in the project folder.
2. Run: python build.py
3. The compiler will gather all resources and create a single file in the dist/ directory.

## License
Licensed under the MIT License.
