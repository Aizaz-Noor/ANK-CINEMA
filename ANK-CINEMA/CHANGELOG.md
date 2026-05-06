# Changelog

All notable changes to ANK-Cinema are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [3.0.0] — 2026-05

### Added
- Internal multi-source search engine (TPB via apibay.org + TorrentGalaxy HTML scraper)
- Background metadata warming — pre-announces top 3 results to trackers while user reads table
- Smart diagnostics system — checks connectivity, DNS, disk space, and engine health on startup
- Self-healing DNS for Linux — auto-switches to Cloudflare/Google DNS when ISP blocks resolution
- Remote auto-updater — fetches and hot-patches `ank_cinema_core.py` from GitHub
- GUI folder picker with tkinter fallback to CLI prompt
- Magnet enrichment — bakes 16 HTTPS/HTTP/UDP trackers into bare magnet links
- Cross-platform portable launchers (.bat / .command / .desktop / .sh)
- PyInstaller build pipeline (`build.py`) producing standalone binaries
- Rich TUI with custom theme, seeder health indicators, and structured result tables
- Config persistence via `config/config.json` with merge-on-load defaults
- Error logging to `logs/error.log` with ISO timestamps
- Unit test suite covering pure functions and core logic
- GitHub Actions CI pipeline (lint + 9-combination test matrix + build check)
- pyproject.toml with PEP 517/518 packaging and `ank-cinema` entry point

### Changed
- Replaced `pirate-get` dependency with internal scraper (no external CLI tools required)
- Switched tracker ordering: HTTPS-first to bypass ISP UDP blocks
- aria2c now receives enriched magnets instead of bare ones — eliminates metadata stall

### Removed
- `pirate-get` runtime dependency
- External tool dependency for search

---

## [2.0.0] — 2025

### Added
- Multi-source search fallback
- aria2c auto-installation for Windows, macOS, Linux
- Background process cleanup on Ctrl+C

### Changed
- Rewrote launcher scripts for better cross-platform compatibility

---

## [1.0.0] — 2024

- Initial release — single-source search + aria2c download
