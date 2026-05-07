<div align="center">

# ANK-Cinema

**A terminal-based movie & series downloader for Linux, Windows, and macOS**

[![CI](https://github.com/Aizaz-Noor/ANK-CINEMA/actions/workflows/ci.yml/badge.svg)](https://github.com/Aizaz-Noor/ANK-CINEMA/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue?logo=python&logoColor=white)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)](#quick-start)
[![Tests](https://img.shields.io/badge/tests-18%20passing-brightgreen)](#development)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-orange)](https://github.com/astral-sh/ruff)
[![Version](https://img.shields.io/badge/version-3.0.1-blue)](#changelog)

</div>

<br>
<div align="center">
  https://github.com/user-attachments/assets/a2625fe2-cc5f-4a97-afd2-f05ad4c35e6e
</div>

---

ANK-Cinema is a self-contained command-line tool. Double-click the launcher for your OS, type a title, pick a result from the colour-coded table, and `aria2c` starts a parallel, multi-connection download. No configuration needed on first run. The app creates its own virtual environment, installs its own dependencies, and never touches your system Python.

---

## Table of Contents

- [Quick Start](#quick-start)
- [How It Works](#how-it-works)
  - [Parallel search](#parallel-search)
  - [Magnet enrichment](#magnet-enrichment)
  - [Smart diagnostics](#smart-diagnostics)
  - [Self-healing DNS](#self-healing-dns-linux-only)
  - [Portable bootstrapper](#portable-bootstrapper)
  - [Remote auto-updater](#remote-auto-updater)
- [Configuration](#configuration)
- [File Structure](#file-structure)
- [Development](#development)
- [CI Pipeline](#ci-pipeline)
- [Tech Stack](#tech-stack)
- [License](#license)

---

## Quick Start

Clone the repo, then run the launcher for your OS. That is all.

```bash
git clone https://github.com/Aizaz-Noor/ANK-CINEMA.git
cd ANK-CINEMA/ANK-CINEMA
```

| Platform | File | How |
|:---------|:-----|:----|
| Windows  | `ANK-CINEMA.bat` | Double-click |
| macOS    | `ANK-CINEMA.command` | Double-click |
| Linux    | `ANK-CINEMA-launcher.sh` | `bash ANK-CINEMA-launcher.sh` |

On first launch, the script creates a `.venv` inside the project folder and installs `requests` and `rich`. Nothing is installed globally. Every launch after that goes straight to the app.

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

The search layer fires two scrapers at the same time using `ThreadPoolExecutor`. One hits the apibay.org JSON API (The Pirate Bay data). The other scrapes TorrentGalaxy HTML. Both run in separate threads.

```
query
 ├─► scrape_apibay()   [TPB JSON API]  ─┐
 └─► scrape_tgx()      [TGX HTML]      ─┴─► deduplicate by info_hash ─► sort by seeders
```

Once both threads return, results are deduplicated by BitTorrent info-hash so the same torrent from two sources appears only once. The list is then sorted by seeder count, highest first. A colour-coded health indicator (`Excellent / Good / Low`) is shown next to each row.

`asyncio` was not used. For two concurrent I/O calls in a synchronous CLI, `ThreadPoolExecutor` has lower overhead and is easier to follow.

---

### Magnet enrichment

A bare magnet link contains only an info-hash:

```
magnet:?xt=urn:btih:AABBCCDDEEFF...
```

With no tracker list, `aria2c` has to find peers through DHT alone. DHT works over UDP, which many ISPs block or throttle. `enrich_magnet()` appends 16 tracker URLs to every magnet before it reaches `aria2c`, ordered HTTPS-first so the connection works even under strict firewall rules:

```
magnet:?xt=urn:btih:HASH
  &tr=https://tracker.opentrackr.org:1337/announce
  &tr=https://opentracker.i2p.rocks:443/announce
  &tr=http://tracker.openbittorrent.com:80/announce
  &tr=udp://tracker.opentrackr.org:1337/announce
  ... (16 total)
```

This is the main reason downloads start fast instead of stalling at `[METADATA]`. The tracker list is deduplicated on every call so running `enrich_magnet` twice does not double the tracker count.

---

### Smart diagnostics

On every startup, the app runs four checks:

1. **Network connectivity** hits known sites to confirm the network path is open.
2. **DNS resolution** resolves `google.com` to verify DNS is functioning.
3. **Disk space** warns if free space drops below 500 MB.
4. **aria2c availability** confirms the download engine is present and runnable.

If any check fails, a red panel lists the specific issues. On Linux, a DNS failure triggers an optional self-heal prompt.

---

### Self-healing DNS (Linux only)

If the connectivity test passes (a raw IP reaches the internet) but DNS fails, the app offers to fix it automatically:

```
IP ping OK, DNS broken
 └─► chattr -i /etc/resolv.conf
     echo "nameserver 1.1.1.1\nnameserver 8.8.8.8" | sudo tee /etc/resolv.conf
     chattr +i /etc/resolv.conf
```

`chattr +i` locks the file so `NetworkManager` cannot overwrite it on reconnect. This runs only when the user confirms and only on Linux.

---

### Portable bootstrapper

The `.bat`, `.command`, and `.sh` launcher scripts handle first-run setup without assuming anything about the user's environment. Each one:

1. Finds Python without relying on `PATH` order (tries `python`, `python3`, `py` in sequence)
2. Creates a `.venv` inside the project directory if one does not exist
3. Installs `requests` and `rich` into that venv
4. Adds the `bin/` folder (where `aria2c.exe` lives on Windows) to `PATH` for the session
5. Runs `ank_cinema_core.py` with the venv's Python

The tricky parts: Windows codepage 1252 crashes on Unicode output (fixed by wrapping `sys.stdout` in UTF-8 before any import); detecting MSYS2 Python vs native Python; handling partial venvs from interrupted first-runs.

---

### Remote auto-updater

On startup, the app fetches a `VERSION` file from GitHub. If a newer version is found, it offers to hot-patch `ank_cinema_core.py` in place using `os.execv` to restart into the new code immediately. No manual download required.

---

## Configuration

The app writes `config/config.json` on first run. Edit it directly or change settings from the app's folder picker prompt on each download.

| Key | Default | What it controls |
|:----|:--------|:----------------|
| `target_dir` | `~/Movies` | Where files are saved |
| `max_results` | `10` | How many results the table shows |
| `splits` | `16` | aria2c connections per file |
| `max_peers` | `200` | Maximum BitTorrent peers |
| `seed_time` | `0` | Seconds to seed after download finishes |
| `min_split_mb` | `1` | Minimum chunk size for splitting |
| `rd_api_key` | `""` | Real-Debrid API key (reserved for future use) |

The config file is gitignored. Your personal paths and API keys stay local.

---

## File Structure

```
ANK-CINEMA/
├── ank_cinema_core.py           ← the whole app — ~785 lines, nine numbered sections
├── build_binary.py              ← builds a standalone binary via PyInstaller
├── pyproject.toml               ← PEP 517/518 packaging with ank-cinema entry point
├── requirements.txt             ← runtime deps: requests, rich
├── tests/
│   ├── conftest.py              ← blocks real network calls during tests
│   └── test_core.py             ← 18 unit tests across 6 test classes
├── ANK-CINEMA.bat               ← Windows launcher
├── ANK-CINEMA.command           ← macOS launcher
├── ANK-CINEMA-launcher.sh       ← Linux launcher
├── ANK-CINEMA.desktop           ← Linux desktop entry
├── INSTALL.md                   ← setup instructions per platform
├── CHANGELOG.md                 ← version history
├── CONTRIBUTING.md              ← dev setup and PR guidelines
└── bin/                         ← aria2c.exe lives here on Windows (not tracked in git)
```

The source is a single file by design. Everything the app does is in `ank_cinema_core.py`. Sections are numbered and commented so any subsystem is findable without a module map.

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
pytest tests/ -v       # 18 tests — no network required
```

All 18 tests run without network access. A `conftest.py` fixture blocks real connections at the socket level so tests are fully deterministic. The test suite covers:

- `health()` — boundary testing of the seeder health indicator
- `enrich_magnet()` — tracker injection and idempotency
- `load_config` / `save_config` — defaults, roundtrip, partial merge, corrupt JSON
- `find_aria2c()` — local bin preference and missing engine fallback
- `search()` — info-hash deduplication and seeder-descending sort

A real bug was caught during development: the upstream apibay API occasionally returns an empty string for file sizes instead of an integer, causing a `ValueError` crash in production. The parser was hardened with `try...except` blocks and safe integer coercion before the v3.0.1 release.

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

**Build check** — builds the wheel with `python -m build` and runs `twine check` to verify the package metadata is valid before any release.

The full matrix is in `.github/workflows/ci.yml`.

---

## Tech Stack

| Tool | Why it is here |
|:-----|:--------------|
| Python 3.8+ | Cross-platform stdlib eliminates most dependencies |
| [Rich](https://github.com/Textualize/rich) | Colour tables, status spinners, panels — no curses complexity |
| requests | HTTP for search API calls, update checks, and TGX scraping |
| [aria2c](https://aria2.github.io/) | Handles BitTorrent, magnets, and multi-connection HTTP with one binary |
| ThreadPoolExecutor | Two parallel search threads — lighter than asyncio for this case |
| tkinter | Native GUI folder picker with CLI fallback |
| [PyInstaller](https://pyinstaller.org/) | Packages the app as a single executable with no Python required |
| ruff | Fast linter, consistent with CI |
| pytest | 18 unit tests covering all pure functions |

---

## License

MIT see [LICENSE](LICENSE).

Built by [Aizaz Noor](https://github.com/Aizaz-Noor).
