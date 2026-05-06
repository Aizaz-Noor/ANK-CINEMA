# ANK-CINEMA v3.0 Portable Installation Guide

This package is designed to work as a portable, one-click product on Windows, macOS, and Linux.

## ✅ What makes this one-click
- Everything stays inside the `ANK-CINEMA/` folder.
- The app creates its own local virtual environment (`.venv`) automatically.
- Required Python packages are installed on first launch.
- No system-wide installation is required.

## Windows
1. Open `ANK-CINEMA/` in File Explorer.
2. Double-click `ANK-CINEMA.bat`.
3. If Python is not installed, the launcher opens the Python download page.
4. On first launch, the launcher builds `.venv` and installs `requests` and `rich`.
5. The app starts immediately after setup.

### Alternative
- If you build a portable executable with `build.py`, double-click the generated `.exe` instead.

## macOS
1. Open `ANK-CINEMA/` in Finder.
2. Double-click `ANK-CINEMA.command`.
3. The app opens in Terminal and runs the portable launcher.
4. If Python 3.8+ is missing, the launcher shows instructions to install it.

## Linux
1. Open `ANK-CINEMA/` in your file manager.
2. Make sure `ANK-CINEMA.desktop` is executable.
   - `chmod +x ANK-CINEMA.desktop`
3. Double-click `ANK-CINEMA.desktop`.
4. If that does not work, open a terminal and run:
   ```bash
   cd /path/to/ANK-CINEMA
   bash ANK-CINEMA-launcher.sh
   ```

## First run experience
- The launcher displays a friendly setup message.
- It creates a local `.venv` folder.
- It installs the required Python dependencies automatically.
- After setup, the app launches the search/download interface.

## Troubleshooting
- If Python is missing, install Python 3.8+ from https://www.python.org/downloads/
- If the app fails to start, delete the `.installed` file and run the launcher again.
- If downloads fail, check `logs/error.log` for details.

## Notes
- The app is portable: you can move the `ANK-CINEMA/` folder to another machine.
- No global PATH changes are required.
- The destination chooser prompts you before every download.
