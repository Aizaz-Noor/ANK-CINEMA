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
  <video src="https://github.com/Aizaz-Noor/ANK-CINEMA/raw/main/assets/demo.mp4" width="800" controls="controls" autoplay loop muted></video>
</div>

---

ANK-Cinema runs from a double-click. It searches multiple torrent indexes in parallel, shows results in a colour-coded table, and hands the chosen magnet to `aria2c`  a download engine it either finds on your system or installs for you. No configuration needed on first run. The app keeps everything inside its own folder and never touches your system Python.

The engineering work that makes this interesting is not the download itself  `aria2c` handles that. It is the pieces around it: the parallel scraper, the background metadata warm-up, the cross-platform bootstrapper, and the magnet enrichment that turns a bare hash into a well-connected download.

---

## Table of Contents

- [Quick Start](#quick-start)
- [How It Works](#how-it-works)
  - [Parallel search](#parallel-search)
  - [Magnet enrichment](#magnet-enrichment)
  - [Self-healing DNS](#self-healing-dns-linux-only)
  - [Portable bootstrapper](#portable-bootstrapper)
- [Configuration](#configuration)
- [File Structure](#file-structure)
- [Development](#development)
- [CI Pipeline](#ci-pipeline)
- [Tech Stack](#tech-stack)
- [License](#license)

---

## Quick Start

Clone the repo, then run the file for your operating system. That is all.

```bash
git clone https://github.com/Aizaz-Noor/ANK-CINEMA.git
cd ANK-CINEMA/ANK-CINEMA
```

| Platform | File | Command |
|:---------|:-----|:--------|
| Windows | `ANK-CINEMA.bat` | Double-click it |
| macOS | `ANK-CINEMA.command` | Double-click it |
| Linux | `ANK-CINEMA-launcher.sh` | `bash ANK-CINEMA-launcher.sh` |

On first launch, the script creates a `.venv` inside the project folder and installs `requests` and `rich`. Nothing is installed globally. On every launch after that, it goes straight to the app.

**Install as a package instead** (if you prefer `pip`):

```bash
cd ANK-CINEMA
pip install -e .
ank-cinema
```

**Build a standalone binary** (no Python required on the target machine):

```bash
python build_binary.py
# Output → dist/ANK-CINEMA  (or ANK-CINEMA.exe on Windows)
```

---

## How It Works

### Parallel search

The search layer sends queries to two independent sources at the same time using `ThreadPoolExecutor`. One hits the apibay.org JSON API (The Pirate Bay's data). The other scrapes TorrentGalaxy's HTML. Both run in separate threads.

```
query
 ├─► scrape_apibay()   [JSON API]   ─┐
 └─► scrape_tgx()      [HTML]       ─┴─► deduplicate by info_hash ─► sort by seeders
```

Once both threads return, results are deduplicated by BitTorrent info-hash so the same torrent from two sources appears only once. The list is then sorted by seeder count, highest first.

`asyncio` was not used here. For two concurrent I/O calls in a synchronous CLI, `ThreadPoolExecutor` has less setup cost and makes the code easier to follow.

---

### Magnet enrichment

A bare magnet link looks like this:

```
magnet:?xt=urn:btih:AABBCCDDEEFF...
```

With no tracker list, `aria2c` has to find peers through DHT alone. DHT works over UDP, which many ISPs block or throttle. The `enrich_magnet()` function appends 16 tracker URLs to every magnet before passing it to `aria2c`. Trackers are ordered HTTPS-first so the connection works even under strict firewall rules.

```
magnet:?xt=urn:btih:HASH
  &tr=https://tracker.opentrackr.org:1337/announce
  &tr=https://opentracker.i2p.rocks:443/announce
  &tr=http://tracker.openbittorrent.com:80/announce
  &tr=udp://tracker.opentrackr.org:1337/announce
  ... (16 total)
```

This is the single biggest reason downloads start fast instead of sitting at `[METADATA]` for minutes.

---

### Self-healing DNS (Linux only)

The startup diagnostics check four things: network connectivity, DNS resolution, disk space, and whether `aria2c` is present. If the connectivity test passes (a raw IP ping works) but DNS fails, the app can fix it.

It writes Cloudflare and Google DNS entries to `/etc/resolv.conf` and uses `chattr +i` to lock the file so `NetworkManager` cannot overwrite them on reconnect. This runs only when the user confirms and only on Linux.

```
IP ping OK, DNS broken
 └─► chattr -i /etc/resolv.conf
     echo "nameserver 1.1.1.1\nnameserver 8.8.8.8" | sudo tee /etc/resolv.conf
     chattr +i /etc/resolv.conf
```

---

### Portable bootstrapper

The `.bat`, `.command`, and `.sh` launcher scripts handle first-run setup without assuming anything about the user's environment. Each one:

1. Finds Python without relying on `PATH` order (tries `python`, `python3`, `py` in sequence)
2. Creates a `.venv` inside the project directory if one does not exist
3. Installs `requests` and `rich` into that venv
4. Adds the `bin/` folder (where `aria2c.exe` lives on Windows) to `PATH` for the session
5. Runs `ank_cinema_core.py` with the venv's Python

The tricky parts were: Windows codepage 1252 crashing on Unicode output (fixed by wrapping `sys.stdout` in UTF-8 before any import), detecting MSYS2 Python vs native Python, and handling partial venvs from interrupted first-runs.

---

## Configuration

The app writes `config/config.json` on first run. Edit it directly or change settings from the app's prompt on each download.

| Key | Default | What it controls |
|:----|:--------|:----------------|
| `target_dir` | `~/Movies` | Where files are saved |
| `max_results` | `10` | How many results the table shows |
| `splits` | `16` | aria2c connections per file |
| `max_peers` | `200` | Maximum BitTorrent peers |
| `seed_time` | `0` | Seconds to seed after download finishes |
| `min_split_mb` | `1` | Minimum chunk size for splitting |
| `rd_api_key` | `""` | Real-Debrid API key (unused in v3.0, reserved) |

The config file is gitignored. Your personal paths and API keys stay local.

---

## File Structure

```
ANK-CINEMA/
├── ank_cinema_core.py       # The whole app — ~780 lines, nine numbered sections
├── build_binary.py                 # Builds a standalone binary via PyInstaller
├── pyproject.toml           # PEP 517/518 packaging, entry point, dev deps
├── requirements.txt         # Runtime deps: requests, rich
│
├── tests/
│   ├── conftest.py          # Blocks real network calls during tests
│   └── test_core.py         # 18 unit tests across 6 test classes
│
├── ANK-CINEMA.bat           # Windows launcher
├── ANK-CINEMA.command       # macOS launcher
├── ANK-CINEMA-launcher.sh   # Linux launcher (bash)
├── ANK-CINEMA.desktop       # Linux desktop entry
│
├── INSTALL.md               # Setup instructions per platform
├── CHANGELOG.md             # Version history
├── CONTRIBUTING.md          # Dev setup and PR guidelines
└── bin/                     # aria2c.exe lives here on Windows (not tracked in git)
```

The source is a single file by design. Everything the app does is in `ank_cinema_core.py`. The sections are numbered and commented so you can find any subsystem quickly without a module map.

---

## Development

```bash
git clone https://github.com/Aizaz-Noor/ANK-CINEMA.git
cd ANK-CINEMA/ANK-CINEMA
pip install -e ".[dev]"
```

This installs the app in editable mode plus `pytest`, `ruff`, and `black`.

**Run the tests:**

```bash
pytest tests/ -v
```

All 18 tests run without network access. A `conftest.py` fixture blocks real connections at the socket level so tests are deterministic. The test suite and bug hunting sweeps found a genuine bug during development: the upstream apibay JSON API occasionally returned empty strings for file sizes, which caused a fatal `ValueError` and crashed the app. The parser was hardened with a robust `try...except` block and dynamic byte-conversion to guarantee stability before final release.

**Lint:**

```bash
ruff check ank_cinema_core.py
```

**Build the binary:**

```bash
python build_binary.py
```

`build_binary.py` downloads `aria2c` for the current platform if it is not already in `bin/`, then runs PyInstaller with `--onefile`. The output is in `dist/`.

---

## CI Pipeline

Every push and pull request triggers three jobs:

**Lint** — runs `ruff` on all Python files.

**Test matrix** — runs `pytest` across 9 combinations: Python 3.9, 3.11, and 3.12 on Ubuntu, Windows, and macOS. All 9 must pass.

**Build check** — builds the wheel with `python -m build` and runs `twine check` to verify the package metadata is valid.

The matrix is in `.github/workflows/ci.yml`.

---

## Tech Stack

| Tool | Why it is here |
|:-----|:--------------|
| Python 3.8+ | Cross-platform stdlib is complete enough to avoid most dependencies |
| [Rich](https://github.com/Textualize/rich) | Coloured tables, status spinners, and panels without curses complexity |
| requests | HTTP for the search API calls and the update check |
| [aria2c](https://aria2.github.io/) | Handles BitTorrent, magnets, and multi-connection HTTP with one binary |
| ThreadPoolExecutor | Two parallel search threads — lighter than asyncio for this case |
| [PyInstaller](https://pyinstaller.org/) | Packages the app into a single executable with no Python required |
| ruff | Linter — catches issues fast, consistent with CI |
| pytest | 18 unit tests covering all pure functions |

---

## License

MIT see [LICENSE](../LICENSE).

Built by [Aizaz Noor](https://github.com/Aizaz-Noor).
