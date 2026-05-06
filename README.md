<div align="center">

# ANK-Cinema

**A terminal-based media downloader for Linux, Windows, and macOS**

[![CI](https://github.com/Aizaz-Noor/ANK-CINEMA/actions/workflows/ci.yml/badge.svg)](https://github.com/Aizaz-Noor/ANK-CINEMA/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue?logo=python&logoColor=white)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)](#quick-start)
[![Tests](https://img.shields.io/badge/tests-18%20passing-brightgreen)](#development)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-orange)](https://github.com/astral-sh/ruff)

</div>

<br>
<div align="center">
  <video src="https://raw.githubusercontent.com/Aizaz-Noor/ANK-CINEMA/main/assets/demo.mp4" width="800" controls muted autoplay loop playsinline></video>
</div>

---

ANK-Cinema runs from a double-click. It searches multiple torrent indexes in parallel, shows results in a colour-coded table, and hands the chosen magnet to `aria2c`  a download engine it either finds on your system or installs for you. No configuration needed on first run. The app keeps everything inside its own folder and never touches your system Python.

The engineering work that makes this interesting is not the download itself  `aria2c` handles that. It is the pieces around it: the parallel scraper, the background metadata warm-up, the cross-platform bootstrapper, and the magnet enrichment that turns a bare hash into a well-connected download.

---

## Quick Start

Clone the repo, then run the launcher for your OS. That is all.

```bash
git clone https://github.com/Aizaz-Noor/ANK-CINEMA.git
cd ANK-CINEMA/ANK-CINEMA
```

| Platform | File | How |
|:---------|:-----|:----|
| Windows | `ANK-CINEMA.bat` | Double-click |
| macOS | `ANK-CINEMA.command` | Double-click |
| Linux | `ANK-CINEMA-launcher.sh` | `bash ANK-CINEMA-launcher.sh` |

First launch creates a `.venv` inside the project folder and installs `requests` and `rich`. Nothing is installed globally.

**Install as a package:**

```bash
cd ANK-CINEMA
pip install -e .
ank-cinema
```

**Build a standalone binary** (no Python required on target machine):

```bash
python ANK-CINEMA/build_binary.py
# Output → ANK-CINEMA/dist/ANK-CINEMA[.exe]
```

---

## How It Works

### Parallel search

The search layer queries two sources at the same time using `ThreadPoolExecutor` — apibay.org (JSON API) and TorrentGalaxy (HTML scraper). Results are deduplicated by BitTorrent info-hash and sorted by seeder count.

```
query
 ├─► scrape_apibay()  [JSON]  ─┐
 └─► scrape_tgx()     [HTML]  ─┴─► deduplicate by info_hash ─► sort by seeders
```

`asyncio` was not used. For two concurrent I/O calls in a synchronous CLI, `ThreadPoolExecutor` has lower overhead and is easier to follow.

### Magnet enrichment

Bare magnet links (`magnet:?xt=urn:btih:HASH`) require DHT to find peers, which is blocked or throttled by many ISPs over UDP. `enrich_magnet()` appends 16 tracker URLs to every magnet before it reaches `aria2c`, ordered HTTPS-first:

```
magnet:?xt=urn:btih:HASH
  &tr=https://tracker.opentrackr.org:1337/announce
  &tr=https://opentracker.i2p.rocks:443/announce
  &tr=http://tracker.openbittorrent.com:80/announce
  &tr=udp://tracker.opentrackr.org:1337/announce
  ... (16 total)
```

This is the single biggest reason downloads start immediately instead of sitting at `[METADATA]`.

### Self-healing DNS (Linux)

If the startup diagnostics detect that a raw IP ping works but DNS fails, the app can fix it: it writes Cloudflare and Google resolvers to `/etc/resolv.conf` and locks the file with `chattr +i` so `NetworkManager` cannot overwrite them on reconnect.

### Portable bootstrapper

The `.bat`, `.command`, and `.sh` launchers handle first-run setup without assuming anything about the environment. Each one finds Python, creates a `.venv` inside the project directory, installs only the two runtime dependencies, and runs the app with the venv's Python. The hard parts were Windows codepage 1252 crashing on Unicode (fixed by wrapping `sys.stdout` in UTF-8 before imports) and detecting partial venvs from interrupted first-runs.

---

## Configuration

Settings persist in `ANK-CINEMA/config/config.json`:

| Key | Default | What it controls |
|:----|:--------|:----------------|
| `target_dir` | `~/Movies` | Where files are saved |
| `max_results` | `10` | Rows shown in the results table |
| `splits` | `16` | aria2c connections per file |
| `max_peers` | `200` | Maximum BitTorrent peers |
| `seed_time` | `0` | Seconds to seed after download finishes |
| `min_split_mb` | `1` | Minimum chunk size for splitting |
| `rd_api_key` | `""` | Real-Debrid API key (reserved, unused in v3.0) |

---

## File Structure

```
ANK-CINEMA/                      ← all source lives here
├── ank_cinema_core.py           ← the whole app — ~780 lines, nine numbered sections
├── build_binary.py                     ← builds a standalone binary via PyInstaller
├── pyproject.toml               ← PEP 517/518 packaging with ank-cinema entry point
├── requirements.txt             ← runtime deps: requests, rich
├── tests/
│   ├── conftest.py              ← blocks real network calls during tests
│   └── test_core.py             ← 18 unit tests across 6 test classes
├── ANK-CINEMA.bat               ← Windows launcher
├── ANK-CINEMA.command           ← macOS launcher
├── ANK-CINEMA-launcher.sh       ← Linux launcher
├── ANK-CINEMA.desktop           ← Linux desktop entry
├── INSTALL.md
├── CHANGELOG.md
└── CONTRIBUTING.md

.github/workflows/ci.yml         ← CI pipeline
```

---

## Development

```bash
git clone https://github.com/Aizaz-Noor/ANK-CINEMA.git
cd ANK-CINEMA/ANK-CINEMA
pip install -e ".[dev]"

pytest tests/ -v       # run 18 tests — no network required
ruff check ank_cinema_core.py
python build_binary.py        # builds dist/ANK-CINEMA[.exe]
```

The test suite and bug hunting sweeps found a real bug during development: the upstream apibay JSON API occasionally returned empty strings for file sizes, which caused a fatal `ValueError` and crashed the app. The parser was hardened with a robust `try...except` block and dynamic byte-conversion to guarantee stability before final release.

---

## CI Pipeline

Every push runs three jobs:

- **Lint** — ruff on all Python files
- **Test matrix** — pytest across 9 combinations: Python 3.9, 3.11, 3.12 on Ubuntu, Windows, and macOS
- **Build check** — builds the wheel and runs `twine check`

---

## Tech Stack

| Tool | Why it is here |
|:-----|:--------------|
| Python 3.8+ | Cross-platform stdlib avoids most dependencies |
| [Rich](https://github.com/Textualize/rich) | Colour tables and spinners without curses |
| requests | HTTP for search API calls and update checks |
| [aria2c](https://aria2.github.io/) | Handles BitTorrent, magnets, and multi-connection HTTP |
| ThreadPoolExecutor | Two parallel search threads |
| [PyInstaller](https://pyinstaller.org/) | Single-file executable, no Python required |
| ruff | Linter |
| pytest | 26 unit tests |

---

## License

MIT see [LICENSE](LICENSE).  
Built by [Aizaz Noor](https://github.com/Aizaz-Noor).
