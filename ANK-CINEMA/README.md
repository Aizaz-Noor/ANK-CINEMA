# ANK-CINEMA v3.0

ANK-Cinema is a tool for searching and downloading movies and series. It's designed to be portable and easy to run without manual setup.

### Features

- **Built-in Search**: Searches multiple sites like TPB and TorrentGalaxy at the same time.
- **Portable**: Everything stays in the project folder. No system-wide installation needed.
- **Auto-Fix**: Automatically handles common DNS and ISP blocks.
- **Fast Downloads**: Uses aria2c for downloading.
- **Updates**: Includes a system to update scrapers when sites change.

### Quick Start

Run the file for your operating system:

| System | File to Run |
| :--- | :--- |
| **Windows** | `ANK-CINEMA.exe` or `ANK-CINEMA.bat` |
| **macOS** | `ANK-CINEMA.command` |
| **Linux** | `ANK-CINEMA.desktop` |

### How it Works

1. **Setup**: On first run, it creates a local environment and downloads required tools.
2. **Search**: Enter a movie name. It will suggest corrections if you misspell it.
3. **Download**: Pick the quality you want and the download starts.

### Configuration

You can change settings in `config/config.json`:
- **Download Path**: Where files are saved.
- **Max Results**: How many search results to show.
- **Real-Debrid**: Add your API key for cached downloads.

### Support

If a search site goes down, the app will try a fallback. If something breaks, check `logs/error.log` for details.

### Building from source

To create your own standalone binary:
```bash
python build.py
```
The output will be in the `dist/` folder.

## License
MIT License. Created by [Aizaz-Noor](https://github.com/Aizaz-Noor).

