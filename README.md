# ANK-Cinema Architect v2.0

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12%2B-blue?logo=python&logoColor=white" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/Powered%20by-aria2c-orange" alt="aria2c">
  <img src="https://img.shields.io/github/stars/Aizaz-Noor/ANK-CINEMA?style=social" alt="GitHub Stars">
</p>

ANK-Cinema is a high-performance, cross-platform command-line utility designed for highly concurrent P2P downloads. It leverages `aria2c` as a headless background daemon to maximize network utilization and minimize connection latency. 

Built with Python, it is tailored for power users who value terminal efficiency, speed, and clean architectural design over traditional graphical interfaces.

<p align="center">
  <img src="demo.gif" alt="ANK-Cinema Demo" width="100%">
</p>

## 🚀 Key Technical Features

- **Maximized Concurrency**: Orchestrates `aria2c` to establish up to 16 simultaneous split connections per file, effectively saturating high-bandwidth gigabit connections.
- **Zero-Latency Handshake**: Implements asynchronous metadata resolution. Background processes pre-negotiate DHT routing and resolve `.torrent` files while you are still browsing results, eliminating the standard 10-15 second startup delay.
- **Smart Prioritization**: Automatically applies `--bt-prioritize-piece=head,tail` to prioritize the beginning and end of files, enabling faster media previewing.
- **Advanced Fallback Logic**: Features recursive query fallback and dynamic DNS self-healing (Linux) to ensure connectivity even in restricted or ISP-throttled environments.
- **Multi-Platform Core**: A unified Python engine (`ank_cinema_core.py`) ensures identical performance and UI behavior across Linux, Windows, and macOS.

## 🛠️ Installation

### Prerequisites
You must have `aria2c` installed on your system:
- **Ubuntu/Debian**: `sudo apt install aria2`
- **macOS**: `brew install aria2`
- **Windows**: `winget install aria2.aria2`

### Using pip (Recommended)
```bash
pip install ank-cinema
```
*Note: On some Linux distributions, you may need to use `pip install ank-cinema --break-system-packages` or `pipx install ank-cinema`.*

### From Source
```bash
git clone https://github.com/Aizaz-Noor/ANK-CINEMA.git
cd ANK-CINEMA
pip install -e .
```

## ⌨️ Usage

Launch the interactive terminal interface:
```bash
ank-cinema
```

The tool will guide you through searching and selecting the optimal download. Your preferences (target directory, peer limits, etc.) are persisted in `~/.ank-cinema/config.json`.

## ⚙️ Configuration

| Parameter | Default | Description |
|---|---|---|
| `target_dir` | `~/Movies` | Destination path for all downloads |
| `max_results` | `10` | Number of results to display in the TUI |
| `splits` | `16` | Number of concurrent connections per file |
| `max_peers` | `200` | Maximum BitTorrent peer limit |
| `seed_time` | `0` | Seeding duration in minutes (0 = disable) |

## 🏗️ System Architecture

1. **Discovery Layer**: Interfaces with decentralized trackers using `pirate-get` with JSON-stream parsing.
2. **Resolution Layer**: Detached background workers pre-announce magnet hashes to the network to resolve metadata into the local file system.
3. **Execution Layer**: The primary engine loads pre-resolved `.torrent` data and executes high-speed multi-threaded retrieval with optimized chunk sizes.

## 🗺️ Roadmap
- [x] v2.0: Unified Python Core & TUI
- [x] v2.0: Background Metadata Warming
- [ ] v2.1: Real-Debrid API Integration for instant cached downloads
- [ ] v2.2: Automated Subtitle Retrieval via OpenSubtitles API
- [ ] v2.3: Watchlist Monitoring & Auto-downloading

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
<p align="center">
  Built for speed by <b>Aizaz Noor</b>
</p>
