#!/usr/bin/env python3
# ANK-CINEMA v3.0
# Movie & Series Downloader for Windows, Linux, and macOS
# Author: Aizaz Noor
# GitHub: https://github.com/aizaznoor/ANK-CINEMA
# License: MIT


import json
import io
import os
import platform
import subprocess
import sys
import shutil
import signal
import tempfile
import time
import hashlib
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# ── Fix: Windows Unicode/emoji crash ─────────────────────────
# Must run before any output and before rich is imported.
# Fixes UnicodeEncodeError on cp1252/cp850 Windows terminals.
if platform.system() == "Windows":
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# ── Enhanced signal handler for graceful cleanup ──────────────
_bg_pids: list[int] = []
_cleanup_done = False

def _signal_cleanup(signum, frame):
    """Gracefully terminate background processes and exit."""
    global _cleanup_done
    if _cleanup_done:
        return
    _cleanup_done = True
    
    for pid in _bg_pids:
        try:
            if platform.system() == "Windows":
                os.kill(pid, signal.SIGBREAK)
            else:
                os.kill(pid, signal.SIGTERM)
        except (ProcessLookupError, OSError):
            pass
    
    sys.exit(0)

signal.signal(signal.SIGINT, _signal_cleanup)
signal.signal(signal.SIGTERM, _signal_cleanup)

# ── Fix: add project dir to PATH so bundled aria2c.exe ───────
# is found without any manual PATH editing by the user.
_SCRIPT_DIR = Path(__file__).parent.resolve()
if str(_SCRIPT_DIR) not in os.environ.get("PATH", ""):
    os.environ["PATH"] = str(_SCRIPT_DIR) + os.pathsep + os.environ.get("PATH", "")

# Setup dependencies
def _pip(*packages: str) -> None:
    args = [sys.executable, "-m", "pip", "install", "--quiet"]
    if platform.system() != "Windows":
        args.append("--break-system-packages")
    args.extend(packages)
    subprocess.run(args, check=False)

for _pkg in ("requests", "rich"):
    try:
        __import__(_pkg)
    except ImportError:
        print(f"[setup] Installing {_pkg}...")
        _pip(_pkg)

import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.rule import Rule
from rich.theme import Theme
from rich.progress import Progress, BarColumn, TimeRemainingColumn, TextColumn
from rich import box as rbox

# Constants
VERSION        = "3.0.0"
API_VERSION    = "3.0"  # For backward compatibility with future versions
OS             = platform.system()          # "Linux" | "Windows" | "Darwin"
TEMP_DIR       = Path(tempfile.gettempdir())
RESULTS_F      = _SCRIPT_DIR / "ank_results.json"
CONFIG_D       = _SCRIPT_DIR / "config"
CONFIG_F       = CONFIG_D / "config.json"
HISTORY_F      = _SCRIPT_DIR / "history.json"
LOGS_D         = _SCRIPT_DIR / "logs"
REQUEST_TIMEOUT = 10  # seconds

# Ordered: HTTPS first (ISP-friendly, bypass UDP blocks),
# then HTTP, then UDP (fast but blocked by many ISPs).
# This order matters — aria2c tries them in sequence.
TRACKERS_LIST = [
    # ── HTTPS (works even with strict ISP/firewall) ───────
    "https://tracker.opentrackr.org:1337/announce",
    "https://opentracker.i2p.rocks:443/announce",
    "https://tracker1.520.jp:443/announce",
    "https://tracker.tamersunion.org:443/announce",
    "https://tracker2.dler.org:80/announce",
    # ── HTTP ──────────────────────────────────────────────
    "http://tracker.openbittorrent.com:80/announce",
    "http://tracker3.itzmx.com:6961/announce",
    "http://tracker.gbitt.info:80/announce",
    # ── UDP (fast, may be blocked by ISP) ─────────────────
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://open.demonii.com:1337/announce",
    "udp://tracker.openbittorrent.com:6969/announce",
    "udp://exodus.desync.com:6969/announce",
    "udp://tracker.torrent.eu.org:451/announce",
    "udp://tracker.moeking.me:6969/announce",
    "udp://tracker1.bt.moack.co.kr:80/announce",
    "udp://tracker.tiny-vps.com:6969/announce",
]

TRACKERS = ",".join(TRACKERS_LIST)

DEFAULT_CFG: dict = {
    "target_dir"  : str(Path.home() / "Movies"),
    "rd_api_key"  : "",
    "max_results" : 10,
    "splits"      : 16,
    "max_peers"   : 200,
    "seed_time"   : 0,
    "min_split_mb": 1,
}

# Rich theme
_theme = Theme({
    "info"       : "cyan",
    "warn"       : "yellow",
    "err"        : "bold red",
    "ok"         : "bold green",
    "h.hi"       : "bold green",
    "h.mid"      : "bold yellow",
    "h.lo"       : "bold red",
    "title"      : "bold white",
    "dim"        : "dim white",
    "hdr"        : "bold cyan",
    "accent"     : "bold magenta",
})
console = Console(theme=_theme, highlight=False)

# Diagnostics
def run_diagnostics() -> dict:
    results = {"ok": True, "issues": []}
    
    # 1. Connectivity
    if not site_reachable():
        results["ok"] = False
        results["issues"].append("ISP/Network is blocking torrent sites.")
        
    # 2. DNS
    try:
        import socket
        socket.gethostbyname("google.com")
    except Exception:
        results["ok"] = False
        results["issues"].append("DNS resolution failed. Check your router/ISP.")
        
    # 3. Disk Space
    try:
        usage = shutil.disk_usage(_SCRIPT_DIR)
        if usage.free < 500 * 1024**2: # < 500MB
            results["ok"] = False
            results["issues"].append("Disk space is dangerously low (< 500MB).")
    except Exception:
        pass
        
    # 4. Engine Health
    if not find_aria2c():
        results["ok"] = False
        results["issues"].append("aria2c engine is missing or corrupted.")
        
    return results

def show_diagnostics():
    with console.status("[info]Running system diagnostics...[/]"):
        diag = run_diagnostics()
    if not diag["ok"]:
        console.print(Panel(
            "\n".join([f"• {i}" for i in diag["issues"]]),
            title="[err]System Issues Detected[/]",
            border_style="red"
        ))
        if any("DNS" in i for i in diag["issues"]):
            if Prompt.ask("Attempt DNS auto-fix?", choices=["y", "n"], default="y") == "y":
                heal_dns()
    return diag["ok"]

# Update system
def check_for_updates():
    """Check for new version and prompt user to update."""
    try:
        # Fetch version from GitHub with retry
        def fetch_version():
            return requests.get(
                "https://raw.githubusercontent.com/aizaznoor/ANK-CINEMA/main/VERSION",
                timeout=REQUEST_TIMEOUT
            )
        
        r = call_with_retry(fetch_version)
        remote_version = r.text.strip()
        if remote_version != VERSION:
            console.print(f"\n[accent]✨ New version {remote_version} available! (Current: {VERSION})[/]")
            if Prompt.ask("Update core engine now?", choices=["y", "n"], default="y") == "y":
                update_self()
    except Exception as e:
        log_error(f"Update check failed: {e}")
        pass

def update_self():
    """Safely update to new version with rollback capability."""
    try:
        import shutil as sh
        backup_path = Path(__file__).with_suffix('.py.bak')
        
        # Create backup
        sh.copy2(__file__, backup_path)
        console.print("[info]Backup created[/]")
        
        # Download new version
        console.print("[info]Downloading update...[/]")
        def fetch_update():
            return requests.get(
                "https://raw.githubusercontent.com/aizaznoor/ANK-CINEMA/main/ANK-CINEMA/ank_cinema_core.py",
                timeout=REQUEST_TIMEOUT
            )
        
        r = call_with_retry(fetch_update)
        if r.status_code != 200:
            raise Exception(f"Failed to download: HTTP {r.status_code}")
        
        new_code = r.content
        
        # Validate syntax before writing
        try:
            compile(new_code, '<string>', 'exec')
        except SyntaxError as e:
            raise Exception(f"New version has syntax error: {e}")
        
        # Write and cleanup backup on success
        with open(__file__, 'wb') as f:
            f.write(new_code)
        
        backup_path.unlink(missing_ok=True)
        console.print("[ok]Update applied successfully! Restarting...[/]")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        # Attempt restore from backup
        backup_path = Path(__file__).with_suffix('.py.bak')
        if backup_path.exists():
            sh.copy2(backup_path, __file__)
            console.print(f"[warn]Restored from backup due to error: {e}[/]")
        else:
            log_error(f"Update failed and no backup available: {e}")
            console.print(f"[err]Update failed: {e}[/]")

# ──────────────────────────────────────────────────────────
# 1.7 LOGGING & RETRY UTILITIES
# ──────────────────────────────────────────────────────────
def log_error(msg: str):
    try:
        LOGS_D.mkdir(exist_ok=True)
        with open(LOGS_D / "error.log", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] {msg}\n")
    except Exception:
        pass

def call_with_retry(fn, max_retries=3, backoff=2.0, timeout_override=None):
    """Retry network operations with exponential backoff and timeout."""
    for attempt in range(max_retries):
        try:
            return fn(timeout=timeout_override or REQUEST_TIMEOUT)
        except (requests.Timeout, requests.ConnectionError) as e:
            if attempt == max_retries - 1:
                raise
            wait_time = backoff ** attempt
            console.print(f"[warn]Network issue. Retrying in {wait_time:.0f}s... (attempt {attempt+1}/{max_retries})[/]")
            time.sleep(wait_time)
        except Exception:
            raise

def verify_download(file_path: Path, expected_size: int = None) -> str:
    """Verify downloaded file integrity. Returns SHA256 hash."""
    if not file_path.exists():
        raise FileNotFoundError(f"Download missing: {file_path}")
    
    actual_size = file_path.stat().st_size
    if expected_size and actual_size != expected_size:
        raise ValueError(f"Size mismatch: expected {expected_size}, got {actual_size}")
    
    # Calculate SHA256
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()

def heal_dns():
    """Fix DNS issues on all platforms (improved cross-platform support)."""
    try:
        if OS == "Windows":
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True, timeout=5)
            console.print("[ok]DNS cache flushed (Windows)[/]")
        elif OS == "Darwin":  # macOS
            subprocess.run(["sudo", "dscacheutil", "-flushcache"], capture_output=True, timeout=5)
            console.print("[ok]DNS cache flushed (macOS)[/]")
        else:  # Linux
            subprocess.run(["sudo", "systemctl", "restart", "systemd-resolved"], capture_output=True, timeout=5)
            console.print("[ok]DNS restarted (Linux)[/]")
    except Exception as e:
        console.print(f"[warn]DNS healing skipped: {e}[/]")
        log_error(f"DNS healing failed: {e}")


# Config management
def load_config() -> dict:
    """Load config from file or run first-time setup."""
    CONFIG_D.mkdir(parents=True, exist_ok=True)
    if not CONFIG_F.exists():
        return first_run_setup()
    try:
        saved = json.loads(CONFIG_F.read_text())
        return {**DEFAULT_CFG, **saved}
    except Exception:
        console.print("[warn]Config corrupted. Starting fresh setup.[/]")
        CONFIG_F.unlink(missing_ok=True)
        return first_run_setup()

def first_run_setup() -> dict:
    """Guided interactive setup on first launch."""
    console.clear()
    console.print(Panel(
        "Welcome to ANK-CINEMA! Let's configure your preferences.",
        title="[bold green]✨ First Run Setup[/]",
        border_style="bold green"
    ))
    
    # Target directory
    default_target = str(Path.home() / "Movies")
    target = Prompt.ask(
        "\n[cyan]📁 Download location[/]",
        default=default_target
    ).strip()
    
    # Max results
    max_results_input = Prompt.ask(
        "[cyan]📊 Max search results per query[/]",
        default="10"
    ).strip()
    try:
        max_results = int(max_results_input)
        if max_results < 1:
            max_results = 10
    except ValueError:
        max_results = 10
    
    # Build config
    cfg = {
        **DEFAULT_CFG,
        "target_dir": target,
        "max_results": max_results
    }
    
    save_config(cfg)
    
    console.print(f"\n[ok]✓ Setup complete![/]")
    console.print(f"[dim]Settings saved to {CONFIG_F}[/]\n")
    
    return cfg

def save_config(cfg: dict) -> None:
    CONFIG_D.mkdir(parents=True, exist_ok=True)
    try:
        CONFIG_F.write_text(json.dumps(cfg, indent=2))
    except Exception as e:
        console.print(f"[warn]Failed to save config: {e}[/]")
        log_error(f"Config save failed: {e}")


# Dependencies
def _which(name: str) -> str | None:
    return shutil.which(name)

def find_aria2c() -> str | None:
    # 1. Local bin folder (V3 Standard)
    local_bin = _SCRIPT_DIR / "bin" / ("aria2c.exe" if OS == "Windows" else "aria2c")
    if local_bin.exists():
        return str(local_bin)
    # 2. System PATH
    found = _which("aria2c")
    if found:
        return found
    # 3. Bundled in root (V2 Legacy)
    legacy = _SCRIPT_DIR / ("aria2c.exe" if OS == "Windows" else "aria2c")
    if legacy.exists():
        return str(legacy)
    return None

def _install_aria2c() -> None:
    console.print("[warn]Installing aria2c...[/]")
    if OS == "Linux":
        subprocess.run(["sudo", "apt-get", "install", "-y", "aria2"],
                       check=False)
    elif OS == "Darwin":
        subprocess.run(["brew", "install", "aria2"], check=False)
    elif OS == "Windows":
        for mgr, cmd in [
            ("winget", ["winget", "install", "-e", "--id", "aria2.aria2", "--silent"]),
            ("scoop",  ["scoop", "install", "aria2"]),
            ("choco",  ["choco", "install", "aria2", "-y"]),
        ]:
            if _which(mgr):
                subprocess.run(cmd, check=False)
                return
        console.print("[err]No package manager found.[/]")
        console.print("[info]Download aria2c from https://github.com/aria2/aria2/releases[/]")

def check_deps() -> bool:
    if not find_aria2c():
        _install_aria2c()
        if not find_aria2c():
            console.print("[err]aria2c missing. Install it or check 'bin' folder.[/]")
            return False
    return True


# Network helpers
def site_reachable() -> bool:
    for url in ["https://1337x.to", "https://thepiratebay.org"]:
        try:
            requests.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            return True
        except Exception:
            continue
    return False

def fetch_trackers() -> list[str]:
    """Fetch tracker list from remote CDN. Falls back to hardcoded list."""
    try:
        def fetch_remote():
            return requests.get(
                "https://raw.githubusercontent.com/aizaznoor/ANK-CINEMA/main/trackers.txt",
            )
        
        r = call_with_retry(fetch_remote, max_retries=2)
        if r.status_code == 200:
            trackers = [line.strip() for line in r.text.split('\n') if line.strip()]
            if trackers:
                return trackers
    except Exception as e:
        log_error(f"Failed to fetch remote trackers: {e}")
    
    # Fallback to hardcoded list
    return TRACKERS_LIST

def get_tracker_string() -> str:
    """Return the current tracker list as a comma-separated string."""
    return ",".join(fetch_trackers())

class DownloadHistory:
    def __init__(self):
        self.history_file = HISTORY_F

    def load(self) -> list[dict]:
        if self.history_file.exists():
            try:
                return json.loads(self.history_file.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def add(self, title: str, magnet: str, status: str) -> None:
        history = self.load()
        history.append({
            "title": title,
            "magnet": magnet,
            "status": status,
            "timestamp": datetime.now().isoformat()
        })
        history = history[-100:]
        try:
            self.history_file.write_text(json.dumps(history, indent=2), encoding="utf-8")
        except Exception as e:
            log_error(f"Failed to save download history: {e}")


def run_aria2_with_progress(cmd: list[str]) -> int:
    """Run aria2c and display progress via Rich."""
    progress = Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        transient=True,
    )
    task_id = progress.add_task("Downloading", total=100)
    with progress:
        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )
        if p.stdout is None:
            return p.wait()
        import re
        for line in p.stdout:
            match = re.search(r"(\d{1,3}(?:\.\d+)?)%", line)
            if match:
                percent = float(match.group(1))
                progress.update(task_id, completed=min(percent, 100.0))
        return p.wait()


def google_suggest(query: str) -> list[str]:
    try:
        def fetch_suggestions():
            return requests.get(
                "https://suggestqueries.google.com/complete/search",
                params={"client": "firefox", "q": query},
                timeout=REQUEST_TIMEOUT
            )
        
        r = call_with_retry(fetch_suggestions, max_retries=2)
        data = r.json()
        return list(data[1])[:5] if len(data) > 1 else []
    except Exception:
        return []


# ──────────────────────────────────────────────────────────
# 5. SEARCH (INTERNAL MULTI-SOURCE ENGINE)
# ──────────────────────────────────────────────────────────
def _size_to_bytes(size_str: str) -> int:
    """Convert size string (e.g. '1.5 GiB') to bytes for sorting."""
    size_str = size_str.lower().replace("b", "").strip()
    multipliers = {"k": 1024, "m": 1024**2, "g": 1024**3, "t": 1024**4}
    for unit, mult in multipliers.items():
        if unit in size_str:
            try:
                return int(float(size_str.replace(unit, "").strip()) * mult)
            except ValueError:
                return 0
    try:
        return int(size_str)
    except ValueError:
        return 0

def scrape_apibay(query: str) -> list[dict]:
    """Search The Pirate Bay via apibay.org JSON API."""
    try:
        r = requests.get(f"https://apibay.org/q.php?q={query}", timeout=REQUEST_TIMEOUT)
        data = r.json()
        if not data or not isinstance(data, list) or "no results" in str(data[0]).lower():
            return []
        results = []
        for item in data:
            results.append({
                "name"    : item.get("name", "Unknown"),
                "size"    : f"{round(int(item.get('size', 0))/(1024**3), 2)} GiB",
                "seeders" : int(item.get("seeders", 0)),
                "leechers": int(item.get("leechers", 0)),
                "magnet"  : f"magnet:?xt=urn:btih:{item.get('info_hash')}&dn={requests.utils.quote(item.get('name',''))}",
                "source"  : "TPB"
            })
        return results
    except Exception:
        return []

def scrape_tgx(query: str) -> list[dict]:
    """Search TorrentGalaxy (fallback scraper)."""
    try:
        url = f"https://torrentgalaxy.to/torrents.php?search={requests.utils.quote(query)}&sort=seeders&order=desc"
        r = requests.get(url, timeout=REQUEST_TIMEOUT, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200: return []
        
        import re
        magnets = re.findall(r'href="(magnet:\?xt=urn:btih:[^"]+)"', r.text)
        names = re.findall(r'title="([^"]+)" class="tx-12"', r.text)
        
        results = []
        for i in range(min(len(magnets), 15)):
            results.append({
                "name"    : names[i] if i < len(names) else "Unknown",
                "size"    : "N/A",
                "seeders" : 0,
                "leechers": 0,
                "magnet"  : magnets[i],
                "source"  : "TGX"
            })
        return results
    except Exception as e:
        log_error(f"TGX Scrape Error: {e}")
        return []

def search(query: str) -> list[dict]:
    """Parallel multi-source search."""
    with console.status(f"[info]Searching for [bold]{query}[/] across engines...[/]"):
        with ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(scrape_apibay, query)
            f2 = executor.submit(scrape_tgx, query)
            
            res1 = f1.result()
            res2 = f2.result()
            
        combined = res1 + res2
        # Deduplicate and sort
        seen = set()
        unique = []
        for r in combined:
            try:
                h = r["magnet"].split("btih:")[1].split("&")[0].lower()
                if h not in seen:
                    seen.add(h)
                    unique.append(r)
            except Exception:
                continue
        
        unique.sort(key=lambda x: x.get("seeders", 0), reverse=True)
        return unique

def search_with_fallback(primary: str, fallback: str = "") -> list[dict]:
    console.print(f"[hdr]Searching:[/] [title]{primary}[/]")
    results = search(primary)
    if not results and fallback and fallback != primary:
        console.print(f"[warn]No results. Trying fallback: {fallback}[/]")
        results = search(fallback)
    return results


# ──────────────────────────────────────────────────────────
# 6. BACKGROUND METADATA WARMING
# ──────────────────────────────────────────────────────────
def warm_trackers(results: list[dict], count: int = 3) -> None:
    """
    Pre-announce to trackers for the top results so the DHT
    table is warm by the time the user picks a download.
    Uses a lightweight aria2c RPC session per magnet — no
    --bt-metadata-only flag because that can lock the info-hash
    and stall the real download when it starts.
    """
    global _bg_pids
    aria2 = find_aria2c()
    if not aria2:
        return
    for item in results[:count]:
        magnet = item.get("magnet", "")
        if not magnet:
            continue
        try:
            # On Windows, we need CREATE_NEW_PROCESS_GROUP to reliably kill via SIGBREAK
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP if OS == "Windows" else 0
            p = subprocess.Popen(
                [
                    aria2,
                    "--enable-dht=true",
                    "--dht-entry-point=router.bittorrent.com:6881",
                    "--enable-peer-exchange=true",
                    "--bt-enable-lpd=true",
                    f"--bt-tracker={get_tracker_string()}",
                    "--bt-save-metadata=true",
                    "--bt-metadata-only=true",
                    f"--dir={TEMP_DIR}",
                    magnet,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creation_flags
            )
            _bg_pids.append(p.pid)
        except Exception:
            pass

def kill_warmers() -> None:
    """Cleanly terminate background tracker warmers."""
    global _bg_pids
    for pid in list(_bg_pids):
        try:
            if OS == "Windows":
                os.kill(pid, signal.SIGBREAK)
            else:
                os.kill(pid, signal.SIGTERM)
        except (ProcessLookupError, OSError):
            pass
    _bg_pids.clear()


# ──────────────────────────────────────────────────────────
# 7. DISPLAY
# ──────────────────────────────────────────────────────────
def health(seeds: int) -> tuple[str, str]:
    if seeds > 50:
        return "h.hi",  "⬤  Excellent"
    if seeds > 10:
        return "h.mid", "◕  Good"
    return "h.lo", "◑  Low / Slow"

def show_banner() -> None:
    console.clear()
    txt = Text()
    txt.append("  🎬  ANK-CINEMA ARCHITECT ", style="bold green")
    txt.append(f"v{VERSION}", style="dim white")
    txt.append("  ·  ", style="dim")
    txt.append("Linux", style="green")
    txt.append(" · ", style="dim")
    txt.append("Windows", style="cyan")
    txt.append(" · ", style="dim")
    txt.append("macOS", style="bold white")
    console.print(Panel(txt, border_style="green", padding=(0, 2)))

def show_results(results: list[dict], max_n: int = 10) -> list[dict]:
    trimmed = results[:max_n]
    console.print()
    console.rule("[bold green]  AVAILABLE DOWNLOADS  [/]", style="green")

    tbl = Table(
        box=rbox.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold cyan",
        show_lines=True,
        expand=True,
        padding=(0, 1),
    )
    tbl.add_column("#",       style="cyan bold",   width=4,  justify="center")
    tbl.add_column("Name",    style="bold white",  ratio=7)
    tbl.add_column("Size",    style="cyan",        ratio=2,  justify="center")
    tbl.add_column("Seeds",   ratio=1,             justify="center")
    tbl.add_column("Health",  ratio=3,             justify="center")

    for i, item in enumerate(trimmed):
        try:
            seeds = int(item.get("seeders", 0))
        except (ValueError, TypeError):
            seeds = 0
        hstyle, hlabel = health(seeds)
        tbl.add_row(
            str(i),
            item.get("name", "Unknown"),
            item.get("size", "?"),
            f"[{hstyle}]{seeds}[/]",
            f"[{hstyle}]{hlabel}[/]",
        )

    console.print(tbl)
    return trimmed


# ──────────────────────────────────────────────────────────
# 8. DOWNLOAD
# ──────────────────────────────────────────────────────────
def enrich_magnet(magnet: str) -> str:
    """
    Append all trackers directly into the magnet URI.

    Why this matters: pirate-get often returns bare magnets
    with only the info-hash (magnet:?xt=urn:btih:HASH) and
    no &tr= params. Without embedded trackers aria2c has to
    rely solely on DHT to find peers — which is slow and
    blocked by many ISPs (especially over UDP).

    By baking every tracker URL into the magnet string,
    aria2c can immediately hit HTTPS/HTTP trackers to resolve
    the metadata, bypassing the DHT cold-start entirely.
    """
    from urllib.parse import quote
    already = magnet.lower()
    additions = []
    for tracker in TRACKERS_LIST:
        encoded = quote(tracker, safe="")
        # Skip if this tracker is already in the magnet
        if encoded.lower() not in already and tracker.lower() not in already:
            additions.append(f"&tr={encoded}")
    return magnet + "".join(additions)

def download(magnet: str, cfg: dict) -> None:
    aria2 = find_aria2c()
    if not aria2:
        console.print("[err]aria2c not found![/]")
        return

    target = str(Path(cfg["target_dir"]).expanduser())
    Path(target).mkdir(parents=True, exist_ok=True)

    console.print()
    info = (
        f"[bold green]🚀 Launching high-speed download[/]\n"
        f"[cyan]📁 Destination :[/] {target}\n"
        f"[yellow]⚡ Splits       :[/] {cfg['splits']}  •  "
        f"[yellow]Peers:[/] {cfg['max_peers']}  •  "
        f"[yellow]Seed-time:[/] {cfg['seed_time']}s"
    )
    console.print(Panel(info, title="[bold]Download Starting[/]", border_style="green"))

    cmd = [
        aria2,
        f"--dir={target}",

        # ── Tracker list ──────────────────────────────────
        f"--bt-tracker={get_tracker_string()}",

        # ── DHT (the fix for CN:0 / SD:0 / DL:0B) ───────
        # Without these, aria2c can't find peers if trackers
        # are slow, giving the [MEMORY][METADATA] stall.
        "--enable-dht=true",
        "--enable-dht6=false",
        "--dht-entry-point=router.bittorrent.com:6881",
        "--dht-entry-point=router.utorrent.com:6881",
        "--dht-entry-point=dht.transmissionbt.com:6881",

        # ── Peer discovery extras ─────────────────────────
        "--enable-peer-exchange=true",   # ask peers for more peers
        "--bt-enable-lpd=true",          # find peers on local network
        "--listen-port=6881-6999",       # open inbound port range

        # ── Metadata ─────────────────────────────────────
        "--bt-save-metadata=true",       # cache for next run
        "--bt-load-saved-metadata=true", # use cache if available

        # ── Speed flags ───────────────────────────────────
        "--bt-prioritize-piece=head,tail",
        f"--max-connection-per-server={cfg['splits']}",
        f"--split={cfg['splits']}",
        f"--min-split-size={cfg['min_split_mb']}M",
        "--max-overall-download-limit=0",
        f"--bt-max-peers={cfg['max_peers']}",
        "--bt-request-peer-speed-limit=100K",

        # ── Misc ──────────────────────────────────────────
        f"--seed-time={cfg['seed_time']}",
        "--file-allocation=none",
        "--summary-interval=3",          # update every 3s (was 5)
        "--console-log-level=notice",
        magnet,
    ]

    if cfg.get("rd_api_key"):
        console.print("[accent]Real-Debrid key detected — instant cache lookup coming in v2.1[/]")

    history = DownloadHistory()
    title = magnet
    if "name" in cfg:
        title = cfg.get("name", magnet)

    try:
        return_code = run_aria2_with_progress(cmd)
        history.add(title, magnet, "completed" if return_code == 0 else f"failed ({return_code})")
        if return_code != 0:
            console.print(f"[err]aria2c exited with code {return_code}.[/]")
    except KeyboardInterrupt:
        history.add(title, magnet, "paused")
        console.print("\n[warn]Download paused by user.[/]")
    except Exception as e:
        history.add(title, magnet, f"failed ({e})")
        console.print(f"[err]Download failed: {e}[/]")


# ──────────────────────────────────────────────────────────
# 9. MAIN INTERACTIVE FLOW
# ──────────────────────────────────────────────────────────
def pick_format() -> tuple[str, str, str]:
    """Return (search_query, fallback_query, format_label)."""
    console.print()
    console.print("[hdr]Format[/]")
    console.print("  [cyan]1.[/] Movie  (English / Global)")
    console.print("  [cyan]2.[/] Series (specific episode)")
    console.print("  [cyan]3.[/] Hindi Dubbed")
    console.print("  [cyan]4.[/] Season Pack")
    fmt = Prompt.ask("Choice", default="1").strip()

    base = _TITLE  # injected before call — see main()

    if fmt == "2":
        s = Prompt.ask("  Season number").strip().zfill(2)
        e = Prompt.ask("  Episode number").strip().zfill(2)
        tag = f"S{s}E{e}"
        return f"{base} {tag}", base, f"Series {tag}"

    if fmt == "3":
        return f"{base} Hindi Dubbed", base, "Hindi Dubbed"

    if fmt == "4":
        s = Prompt.ask("  Season number").strip().zfill(2)
        return f"{base} Season {int(s)} complete", f"{base} S{s}", f"Season {s} Pack"

    return base, "", "Movie"

_TITLE = ""  # global set in main() before pick_format() call

def main() -> None:
    global _TITLE

    # ── Cleanup handler ──────────────────────────────────
    def _cleanup(*_):
        kill_warmers()
        RESULTS_F.unlink(missing_ok=True)
        sys.exit(0)

    signal.signal(signal.SIGINT,  _cleanup)
    signal.signal(signal.SIGTERM, _cleanup)

    cfg = load_config()

    # ── Diagnostics & Updates ────────────────────────────
    show_diagnostics()
    check_for_updates()

    # ── Banner ───────────────────────────────────────────
    show_banner()
    console.print(f"[dim]Platform: {OS}  •  Config: {CONFIG_F}[/]")
    console.print(f"[dim]Target  : {cfg['target_dir']}[/]\n")

    # ── Connectivity check ───────────────────────────────
    # (Simplified since diagnostics handles this now)
    if not site_reachable():
        console.print("[warn]Primary sites unreachable. Trying mirrors...[/]")

    # ── Dependency check ─────────────────────────────────
    if not check_deps():
        sys.exit(1)

    # ── Title input + typo correction ────────────────────
    console.print()
    raw = Prompt.ask("🔎 [bold]Search[/] (e.g. Iron Man)").strip()
    if not raw:
        sys.exit(0)

    console.print("[info]Checking spelling...[/]", end=" ")
    suggestions = google_suggest(raw)
    if suggestions:
        console.print()
        for i, s in enumerate(suggestions, 1):
            console.print(f"  [cyan]{i}.[/] {s}")
        console.print(f"  [cyan]0.[/] Use as-is: '[bold]{raw}[/]'")
        console.print()
        choice = Prompt.ask("Select", default="0").strip()
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(suggestions):
                raw = suggestions[idx - 1]
    else:
        console.print("[ok]OK[/]")

    _TITLE = raw

    # ── Format selection ─────────────────────────────────
    query, fallback, fmt_label = pick_format()
    console.print(f"\n[dim]Format: {fmt_label}  •  Query: {query}[/]\n")

    # ── Search ───────────────────────────────────────────
    results = search_with_fallback(query, fallback)

    if not results:
        console.print("[err]No results found. Try a different spelling or format.[/]")
        sys.exit(1)

    # ── Background metadata warming ──────────────────────
    console.print("[info]Warming up trackers in background...[/]")
    warm_trackers(results)

    # ── Display ──────────────────────────────────────────
    trimmed = show_results(results, cfg["max_results"])

    # ── Selection ────────────────────────────────────────
    console.print()
    sel = Prompt.ask(f"📥 [bold]Select[/] (0–{len(trimmed)-1})").strip()

    if not sel.isdigit() or not (0 <= int(sel) < len(trimmed)):
        console.print("[err]Invalid selection.[/]")
        sys.exit(1)

    chosen = trimmed[int(sel)]
    magnet = chosen.get("magnet", "")
    if not magnet:
        console.print("[err]No magnet link for this entry.[/]")
        sys.exit(1)

    # ── Download ─────────────────────────────────────────
    kill_warmers()
    download(magnet, cfg)

    console.print("\n[ok]Done.[/] Check your Movies folder.")


if __name__ == "__main__":
    main()
