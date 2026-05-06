# Changelog

All notable changes are documented here, newest first.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [3.0.0] — 2026-05

### Added

- **Internal search engine** — replaced `pirate-get` with a parallel scraper that queries apibay.org (JSON) and TorrentGalaxy (HTML) at the same time using `ThreadPoolExecutor`.
- **Background metadata warm-up** — pre-announces the top 3 results to trackers while the user reads the results table, so DHT is already warm when a download starts.
- **Magnet enrichment** — appends 16 HTTPS/HTTP/UDP tracker URLs to bare magnet links before passing them to aria2c. Ordered HTTPS-first to bypass ISP UDP blocks.
- **Smart diagnostics on startup** — checks network connectivity, DNS resolution, disk space, and aria2c availability.
- **Self-healing DNS (Linux)** — if IP connectivity works but DNS is broken, the app can write Cloudflare and Google DNS to `/etc/resolv.conf` and lock the file with `chattr +i`.
- **Remote auto-updater** — checks GitHub for a newer version and hot-patches `ank_cinema_core.py` in place.
- **GUI folder picker** — opens a `tkinter` dialog to choose the download directory; falls back to a CLI prompt if `tkinter` is not available.
- **Rich TUI** — colour-coded results table with seeder health indicators (Excellent / Good / Low).
- **Config persistence** — settings are stored in `config/config.json` and merged with defaults on load, so new keys appear automatically after an update.
- **Error logging** — writes to `logs/error.log` with ISO 8601 timestamps.
- **26-test suite** — covers `_size_to_bytes`, `health`, `enrich_magnet`, `load_config`/`save_config`, `find_aria2c`, and search deduplication. Tests found and fixed a bug in size parsing (see Changed).
- **GitHub Actions CI** — lint (ruff) + 9-combination test matrix (Ubuntu, Windows, macOS × Python 3.9, 3.11, 3.12) + wheel build check.
- **pyproject.toml** — PEP 517/518 packaging with an `ank-cinema` console entry point.
- **Cross-platform launchers** — `.bat` (Windows), `.command` (macOS), `.sh` / `.desktop` (Linux).
- **PyInstaller build pipeline** — `build.py` downloads the correct aria2c binary and produces a single-file executable.

### Fixed

- `_size_to_bytes("1.5 GiB")` was returning `0`. The original code stripped the trailing `b` from "GiB" but then failed to match `"gi"` against the single-character unit keys. Rewrote the suffix-stripping logic to handle both IEC (GiB, MiB, KiB) and SI (GB, MB, KB) notation correctly.

### Changed

- Tracker list ordering changed to HTTPS-first. UDP trackers still included but come last.
- aria2c now receives enriched magnets with all trackers embedded, not bare hashes.
- Removed `pirate-get>=0.3.4` from dependencies — the internal scraper replaced it.

### Removed

- `pirate-get` runtime dependency.
- Stale "coming in v2.1" comment left in v3.0 source.

---

## [2.0.0] — 2025

### Added

- Multi-source search with automatic fallback.
- aria2c auto-installation for Windows (winget/scoop/choco), macOS (brew), and Linux (apt).
- Background process cleanup on Ctrl+C via `signal.SIGTERM`.

### Changed

- Rewrote all launcher scripts for more reliable cross-platform operation.

---

## [1.0.0] — 2024

Initial release. Single-source search and aria2c download.
