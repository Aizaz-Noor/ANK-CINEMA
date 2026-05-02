# ANK-Cinema Architect v2.0

ANK-Cinema is a cross-platform command-line utility for highly concurrent P2P downloads. It orchestrates `aria2c` as a headless background daemon to maximize network utilization and minimize connection latency. 

Built with Python, it is designed for users who prefer efficient terminal environments over graphical interfaces.

## Key Technical Features

- **Concurrent Connections**: Utilizes `aria2c` to establish up to 16 simultaneous split connections, saturating available bandwidth.
- **Asynchronous Metadata Resolution**: Pre-fetches DHT routing tables and BitTorrent metadata in detached background processes during the selection phase, eliminating the standard 10-15 second tracker handshake latency.
- **Sequential Piece Prioritization**: Configured with `--bt-prioritize-piece=head,tail` to prioritize downloading the beginning and end of files first.
- **Network Resilience**: Integrates automatic query fallback algorithms and dynamic DNS routing to bypass restrictive network environments.
- **Cross-Platform Compatibility**: The core application (`ank_cinema_core.py`) is fully compatible with Linux, Windows, and macOS environments.

## Installation

### Using pip (Recommended)
```bash
pip install ank-cinema
```
*Note: `aria2c` must be installed independently on your system (e.g., `sudo apt install aria2` or `brew install aria2`).*

### From Source
```bash
git clone https://github.com/Aizaz-Noor/ANK-CINEMA.git
cd ANK-CINEMA
pip install -e .
```

## Usage

Start the interactive terminal application:
```bash
ank-cinema
```

The interface will prompt you to search and select the desired file. All configuration is handled locally in `~/.ank-cinema/config.json`.

## Configuration Parameters

| Parameter | Default | Description |
|---|---|---|
| `target_dir` | `~/Movies` | Destination path for downloads |
| `max_results` | `10` | Maximum number of search results to display |
| `splits` | `16` | Number of concurrent connections |
| `max_peers` | `200` | Maximum allowed peers per download |
| `seed_time` | `0` | Seeding duration in minutes (0 disables seeding) |

## System Architecture

The application abstracts complex P2P networking concepts into a streamlined CLI tool:
1. **Scraping Layer**: Extracts magnet URIs and parses JSON network data.
2. **Resolution Layer**: Background `aria2c` instances pre-announce to UDP trackers to resolve `.torrent` files asynchronously into the destination directory.
3. **Execution Layer**: The main download process loads the pre-resolved metadata and initiates multi-threaded downloading with optimized chunk sizes.

## License

MIT License.
