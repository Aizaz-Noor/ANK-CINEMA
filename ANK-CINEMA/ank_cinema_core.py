#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║           ANK-CINEMA ARCHITECT v3.0                      ║
║     Cross-Platform Movie & Series Downloader             ║
║     Linux · Windows · macOS  |  One-Click Standalone     ║
╚══════════════════════════════════════════════════════════╝
Author : Aizaz Noor
GitHub : https://github.com/aizaznoor/ANK-CINEMA
License: MIT
"""

import json
from typing import Optional
import io
import os
import platform
import subprocess
import sys
import shutil
import signal
import tempfile
import time
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# ── Fix: Windows Unicode/emoji crash ─────────────────────────
# Must run before any output and before rich is imported.
# Fixes UnicodeEncodeError on cp1252/cp850 Windows terminals.
# Guard: skip when running under pytest (it manages stdout itself).
_under_pytest = "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ
if platform.system() == "Windows" and not _under_pytest:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# ── Fix: add project dir to PATH so bundled aria2c.exe ───────
# is found without any manual PATH editing by the user.
_SCRIPT_DIR = Path(__file__).parent.resolve()
if str(_SCRIPT_DIR) not in os.environ.get("PATH", ""):
    os.environ["PATH"] = str(_SCRIPT_DIR) + os.pathsep + os.environ.get("PATH", "")

# ──────────────────────────────────────────────────────────
# 0. AUTO-INSTALL DEPENDENCIES
# ──────────────────────────────────────────────────────────
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
from rich import box as rbox

# ──────────────────────────────────────────────────────────
# 1. CONSTANTS & GLOBALS
# ──────────────────────────────────────────────────────────
VERSION   = "3.0.0"
OS        = platform.system()          # "Linux" | "Windows" | "Darwin"
TEMP_DIR  = Path(tempfile.gettempdir())
RESULTS_F = _SCRIPT_DIR / "ank_results.json"
CONFIG_D  = _SCRIPT_DIR / "config"
CONFIG_F  = CONFIG_D / "config.json"

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

# ──────────────────────────────────────────────────────────
# 1.5 SMART DIAGNOSTICS
# ──────────────────────────────────────────────────────────
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
        if OS == "Linux" and any("DNS" in i for i in diag["issues"]):
            if Prompt.ask("Attempt DNS auto-fix?", choices=["y", "n"], default="y") == "y":
                heal_dns()
    return diag["ok"]

# ──────────────────────────────────────────────────────────
# 1.6 REMOTE UPDATER
# ──────────────────────────────────────────────────────────
def check_for_updates():
    try:
        # We fetch a small version file from GitHub
        r = requests.get("https://raw.githubusercontent.com/aizaznoor/ANK-CINEMA/main/VERSION", timeout=5)
        if r.status_code != 200:
            return
        remote_version = r.text.strip()
        if not remote_version or remote_version == VERSION:
            return
        console.print(f"\n[accent]✨ New version {remote_version} available! (Current: {VERSION})[/]")
        if Prompt.ask("Update core engine now?", choices=["y", "n"], default="y") == "y":
            update_self()
    except requests.RequestException:
        return
    except Exception as e:
        log_error(f"Update check failed: {e}")
        return

def update_self():
    try:
        console.print("[info]Downloading update...[/]")
        url = "https://raw.githubusercontent.com/aizaznoor/ANK-CINEMA/main/ANK-CINEMA/ank_cinema_core.py"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            with open(__file__, "wb") as f:
                f.write(r.content)
            console.print("[ok]Update applied successfully! Restarting...[/]")
            os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        log_error(f"Update failed: {e}")
        console.print(f"[err]Update failed: {e}[/]")

# ──────────────────────────────────────────────────────────
# 1.7 LOGGING
# ──────────────────────────────────────────────────────────
def log_error(msg: str):
    try:
        log_dir = _SCRIPT_DIR / "logs"
        log_dir.mkdir(exist_ok=True)
        with open(log_dir / "error.log", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] {msg}\n")
    except Exception:
        pass


# ──────────────────────────────────────────────────────────
# 2. CONFIG
# ──────────────────────────────────────────────────────────
def load_config() -> dict:
    CONFIG_D.mkdir(parents=True, exist_ok=True)
    if not CONFIG_F.exists():
        CONFIG_F.write_text(json.dumps(DEFAULT_CFG, indent=2))
        return DEFAULT_CFG.copy()
    try:
        saved = json.loads(CONFIG_F.read_text())
        return {**DEFAULT_CFG, **saved}
    except Exception:
        return DEFAULT_CFG.copy()

def save_config(cfg: dict) -> None:
    CONFIG_D.mkdir(parents=True, exist_ok=True)
    CONFIG_F.write_text(json.dumps(cfg, indent=2))


# ──────────────────────────────────────────────────────────
# 3. DEPENDENCY MANAGEMENT
# ──────────────────────────────────────────────────────────
def _which(name: str) -> Optional[str]:
    return shutil.which(name)

def find_aria2c() -> Optional[str]:
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


# ──────────────────────────────────────────────────────────
# 4. NETWORK
# ──────────────────────────────────────────────────────────
def site_reachable() -> bool:
    for url in ["https://1337x.to", "https://thepiratebay.org"]:
        try:
            requests.get(url, timeout=4, allow_redirects=True)
            return True
        except Exception:
            continue
    return False

def heal_dns() -> bool:
    """Linux-only: switch to Cloudflare/Google DNS."""
    if OS != "Linux":
        return False
    console.print("[warn]DNS self-healing in progress...[/]")
    ping = subprocess.run(["ping", "-c", "1", "8.8.8.8"], capture_output=True)
    if ping.returncode != 0:
        console.print("[err]No internet connection.[/]")
        return False
    try:
        subprocess.run(["sudo", "chattr", "-i", "/etc/resolv.conf"],
                       capture_output=True)
        resolv = "nameserver 1.1.1.1\nnameserver 8.8.8.8\n"
        proc = subprocess.Popen(
            ["sudo", "tee", "/etc/resolv.conf"],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL
        )
        proc.communicate(resolv.encode())
        subprocess.run(["sudo", "chattr", "+i", "/etc/resolv.conf"],
                       capture_output=True)
    except Exception:
        pass
    return site_reachable()

def google_suggest(query: str) -> list[str]:
    try:
        r = requests.get(
            "https://suggestqueries.google.com/complete/search",
            params={"client": "firefox", "q": query},
            timeout=5,
        )
        data = r.json()
        return list(data[1])[:5] if len(data) > 1 else []
    except Exception:
        return []


# ──────────────────────────────────────────────────────────
# 5. SEARCH (INTERNAL MULTI-SOURCE ENGINE)
# ──────────────────────────────────────────────────────────
def scrape_apibay(query: str) -> list[dict]:
    """Search The Pirate Bay via apibay.org JSON API."""
    try:
        r = requests.get(f"https://apibay.org/q.php?q={query}", timeout=10)
        data = r.json()
        if not data or not isinstance(data, list) or "no results" in str(data[0]).lower():
            return []
        results = []
        for item in data:
            try:
                sz_raw = int(item.get("size") or 0)
            except ValueError:
                sz_raw = 0
            
            if sz_raw > 1024**3:
                sz_str = f"{round(sz_raw / (1024**3), 2)} GiB"
            elif sz_raw > 1024**2:
                sz_str = f"{round(sz_raw / (1024**2), 2)} MiB"
            else:
                sz_str = f"{sz_raw} B"
                
            try:
                seeders = int(item.get("seeders") or 0)
            except ValueError:
                seeders = 0
                
            try:
                leechers = int(item.get("leechers") or 0)
            except ValueError:
                leechers = 0

            results.append({
                "name"    : item.get("name", "Unknown"),
                "size"    : sz_str,
                "seeders" : seeders,
                "leechers": leechers,
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
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
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


def choose_download_directory(default_target: str, cfg: dict) -> str:
    """Ask the user to choose a download directory, with GUI fallback."""
    chosen = None
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        chosen = filedialog.askdirectory(
            initialdir=default_target,
            title="Select download folder for ANK-CINEMA",
        )
        root.destroy()
        if chosen:
            chosen = str(Path(chosen).expanduser())
    except Exception:
        chosen = None

    if not chosen:
        console.print(f"[dim]Default download folder: {default_target}[/]")
        if Prompt.ask("Use default download folder?", choices=["y", "n"], default="y") == "y":
            chosen = default_target
        else:
            entered = Prompt.ask("Enter full path to download folder", default=default_target).strip()
            chosen = str(Path(entered).expanduser())

    if chosen and chosen != default_target:
        if Prompt.ask("Save this folder as the new default?", choices=["y", "n"], default="n") == "y":
            cfg["target_dir"] = chosen
            save_config(cfg)

    return chosen


def download(magnet: str, cfg: dict) -> None:
    aria2 = find_aria2c()
    if not aria2:
        console.print("[err]aria2c not found![/]")
        return

    default_target = str(Path(cfg["target_dir"]).expanduser())
    target = choose_download_directory(default_target, cfg)
    if not target:
        console.print("[err]Download cancelled: no destination selected.[/]")
        return

    target = str(Path(target).expanduser())
    Path(target).mkdir(parents=True, exist_ok=True)

    console.print()
    magnet = enrich_magnet(magnet)

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
        f"--bt-tracker={TRACKERS}",

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
        "--bt-request-peer-speed-limit=50M",

        # ── Misc ──────────────────────────────────────────
        f"--seed-time={cfg['seed_time']}",
        "--file-allocation=none",
        "--summary-interval=3",          # update every 3s (was 5)
        "--console-log-level=notice",
        magnet,
    ]

    # Real-Debrid: if API key is set, skip torrent in favour of cached link.
    # The RD unrestrict endpoint returns a direct HTTP download URL which
    # aria2c handles in HTTP mode (faster, no seeding overhead).
    if cfg.get("rd_api_key"):
        console.print("[accent]Real-Debrid key detected — RD cache lookup is on the roadmap.[/]")

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        console.print("\n[warn]Download paused by user.[/]")


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

    def _cleanup(*_):
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
    download(magnet, cfg)

    console.print("\n[ok]Done.[/] Check your Movies folder.")


if __name__ == "__main__":
    main()
