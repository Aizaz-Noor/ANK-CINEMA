# ANK-Cinema

<div align="center">

**Cross-platform CLI download manager with a parallel search engine and rich terminal UI**

[![CI](https://github.com/Aizaz-Noor/ANK-CINEMA/actions/workflows/ci.yml/badge.svg)](https://github.com/Aizaz-Noor/ANK-CINEMA/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue?logo=python&logoColor=white)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)](https://github.com/Aizaz-Noor/ANK-CINEMA)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-orange)](https://github.com/astral-sh/ruff)

</div>

---

## What This Is

ANK-Cinema is a **zero-dependency, fully portable** CLI application that orchestrates a high-performance
download pipeline entirely from the terminal. The goal was to build something that *just works* on any
machine without any configuration — and to push the limits of what a well-engineered Python CLI can do.

> **Scope of what's interesting here:** the parallel search engine, the background metadata warming
> system, the portable virtual environment bootstrapper, and the cross-platform build pipeline.

---

## Key Engineering Decisions

### 1. Parallel Multi-Source Search (`ThreadPoolExecutor`)

The search layer fans out to multiple independent data sources simultaneously:

```
User query
    │
    ├──► scrape_apibay()  ─┐
    │    [JSON API]         ├──► deduplicate by info_hash ──► sort by seeders
    └──► scrape_tgx()    ──┘
         [HTML scraper]
```

Each source runs in its own thread. Results are deduplicated by BitTorrent info-hash before display,
so the same torrent appearing on both sources shows up once.

**Why not async?** For exactly 2 I/O-bound sources, `ThreadPoolExecutor` has lower overhead than
`asyncio` and avoids the event loop complexity in a synchronous CLI context.

---

### 2. Background Metadata Warming

Before the user picks a result, the top 3 are pre-announced to trackers:

```python
# Starts lightweight aria2c sessions for top 3 results
# while the user reads the table — zero perceived wait
warm_trackers(results, count=3)
```

This hides the torrent metadata-resolution latency behind the human "reading time".
When the user selects a result, DHT is already warm and peer connections start immediately.

---

### 3. Portable Bootstrapper (Zero External Dependencies)

The `.bat` / `.command` / `.sh` launchers:
1. Detect the system Python without assuming a PATH
2. Create an isolated `.venv` inside the project folder
3. Install only `requests` and `rich` on first launch
4. Never touch the system Python installation

This is *not* a virtualenv tutorial — the challenge was building a reliable cross-platform
bootstrapper that handles edge cases: missing Python, partial venv, Windows codepage issues,
MSYS2 vs native Python, etc.

---

### 4. Magnet Enrichment

Bare magnets (just `magnet:?xt=urn:btih:HASH`) rely entirely on DHT to find peers, which is
slow and blocked by many ISPs over UDP. The `enrich_magnet()` function bakes all tracker URLs
directly into the magnet string before handing it to `aria2c`:

```python
magnet:?xt=urn:btih:HASH
  &tr=https://tracker.opentrackr.org:1337/announce   # HTTPS — bypasses UDP blocks
  &tr=https://opentracker.i2p.rocks:443/announce
  ... (16 trackers total, HTTPS-first ordered)
```

This converts a potentially stalled download into one that starts immediately via HTTPS trackers,
falling back to UDP/DHT only if needed.

---

### 5. Self-Healing DNS (Linux)

When network diagnostics detect that torrent sites resolve but the user's DNS is broken:

```
ping 8.8.8.8 OK?
    │ yes
    └──► chattr -i /etc/resolv.conf
         write nameserver 1.1.1.1 + 8.8.8.8
         chattr +i /etc/resolv.conf   # lock to prevent NetworkManager override
```

This is a targeted fix that identifies the specific failure mode (working IP connectivity,
broken DNS) and applies the minimal intervention.

---

## Quick Start

No installation required. Just run the launcher for your OS:

| Platform | File | How |
|:---------|:-----|:----|
| Windows | `ANK-CINEMA/ANK-CINEMA.bat` | Double-click |
| macOS | `ANK-CINEMA/ANK-CINEMA.command` | Double-click |
| Linux | `ANK-CINEMA/ANK-CINEMA-launcher.sh` | `bash ANK-CINEMA-launcher.sh` |

First launch builds a local `.venv` and installs dependencies automatically.

**Or install as a Python package:**

```bash
cd ANK-CINEMA
pip install -e .
ank-cinema
```

---

## Architecture

```
ANK-CINEMA/
├── ank_cinema_core.py      # Single-file application core (~833 lines)
│   ├── section 0:  auto-install bootstrap (runs before imports)
│   ├── section 1:  constants, Rich theme, globals
│   ├── section 1.5: smart diagnostics
│   ├── section 1.6: remote updater
│   ├── section 1.7: error logger
│   ├── section 2:  config (load/save JSON)
│   ├── section 3:  dependency management (aria2c detection + install)
│   ├── section 4:  network (site reachability, DNS healing)
│   ├── section 5:  search engine (parallel multi-source)
│   ├── section 6:  background metadata warming
│   ├── section 7:  display (Rich TUI)
│   ├── section 8:  download (magnet enrichment + aria2c orchestration)
│   └── section 9:  interactive main loop
├── build.py                # PyInstaller build pipeline → produces standalone binary
├── pyproject.toml          # PEP 517/518 packaging (pip install, entry_points)
├── requirements.txt        # Pinned runtime dependencies
├── tests/
│   ├── conftest.py         # Global no-network fixture
│   └── test_core.py        # Unit tests (size parsing, health, magnet, config, search)
├── ANK-CINEMA.bat          # Windows portable launcher
├── ANK-CINEMA.command      # macOS portable launcher
├── ANK-CINEMA-launcher.sh  # Linux portable launcher
├── ANK-CINEMA.desktop      # Linux desktop entry
├── config/                 # Runtime config (gitignored)
├── logs/                   # Error logs (gitignored)
└── bin/                    # aria2c engine binary (Windows: aria2c.exe)
```

---

## Configuration

Settings persist in `config/config.json`:

| Key | Default | Description |
|:----|:--------|:------------|
| `target_dir` | `~/Movies` | Default download directory |
| `max_results` | `10` | Search results to display |
| `splits` | `16` | aria2c parallel connections per file |
| `max_peers` | `200` | Maximum BitTorrent peers |
| `seed_time` | `0` | Seconds to seed after completion |
| `min_split_mb` | `1` | Minimum segment size for splitting |
| `rd_api_key` | `""` | Real-Debrid API key (optional) |

---

## Development

```bash
# Clone and set up dev environment
git clone https://github.com/Aizaz-Noor/ANK-CINEMA
cd ANK-CINEMA/ANK-CINEMA
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Lint
ruff check ank_cinema_core.py

# Build standalone binary
python build.py
# Output: dist/ANK-CINEMA[.exe]
```

---

## Technology Stack

| Tool | Role |
|:-----|:-----|
| **Python 3.8+** | Core language — chosen for cross-platform venv support and stdlib completeness |
| **Rich** | Terminal UI — themed console, tables, progress panels |
| **requests** | HTTP — search API calls, update checks |
| **aria2c** | Download engine — handles BitTorrent, magnet links, multi-connection HTTP |
| **ThreadPoolExecutor** | Parallel search — concurrent multi-source fan-out |
| **PyInstaller** | Binary packaging — produces a single-file standalone executable |
| **ruff** | Linting — fast, consistent code style |
| **pytest** | Testing — unit tests for all deterministic functions |

---

## CI

The GitHub Actions pipeline runs on every push:

- **Lint** — ruff on all Python files
- **Test matrix** — Python 3.9, 3.11, 3.12 × Ubuntu, Windows, macOS (9 combinations)
- **Build check** — validates the Python package builds and the wheel passes `twine check`

---

## License

MIT — see [LICENSE](../LICENSE).  
Built by [Aizaz Noor](https://github.com/Aizaz-Noor).
