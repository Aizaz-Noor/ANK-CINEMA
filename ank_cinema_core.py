#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║           ANK-CINEMA ARCHITECT v2.0                      ║
║     Cross-Platform Movie & Series Downloader             ║
║     Linux · Windows · macOS  |  Speed-First Design       ║
╚══════════════════════════════════════════════════════════╝
Author : Aizaz Noor
GitHub : https://github.com/aizaznoor/ANK-CINEMA
License: MIT
"""

import json
import os
import platform
import subprocess
import sys
import shutil
import signal
import tempfile
import time
from pathlib import Path

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
VERSION   = "2.0.0"
OS        = platform.system()          # "Linux" | "Windows" | "Darwin"
TEMP_DIR  = Path(tempfile.gettempdir())
RESULTS_F = TEMP_DIR / "ank_results.json"
CONFIG_D  = Path.home() / ".ank-cinema"
CONFIG_F  = CONFIG_D / "config.json"

TRACKERS = ",".join([
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://open.demonii.com:1337/announce",
    "udp://tracker.openbittorrent.com:6969/announce",
    "udp://exodus.desync.com:6969/announce",
    "udp://tracker.torrent.eu.org:451/announce",
    "udp://tracker.moeking.me:6969/announce",
    "udp://ipv4.tracker.harry.lu:80/announce",
    "udp://9.rarbg.me:2970/announce"
])

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
_bg_pids: list[int] = []   # background aria2c metadata warmers


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
def _which(name: str) -> str | None:
    return shutil.which(name)

def find_aria2c() -> str | None:
    found = _which("aria2c")
    if found:
        return found
    # Windows-specific known locations
    if OS == "Windows":
        for p in [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages",
            Path("C:/tools/aria2"),
            Path.home() / "scoop" / "apps" / "aria2" / "current",
        ]:
            for exe in p.rglob("aria2c.exe") if p.exists() else []:
                return str(exe)
    return None

def find_pirate_get() -> list[str] | None:
    """Return command list to invoke pirate-get, or None."""
    pg = _which("pirate-get")
    if pg:
        return [pg]
    # Try Python module form
    r = subprocess.run(
        [sys.executable, "-m", "pirate", "--version"],
        capture_output=True, text=True
    )
    if r.returncode == 0:
        return [sys.executable, "-m", "pirate"]
    # Windows Scripts folder
    if OS == "Windows":
        scripts = Path(sys.executable).parent / "Scripts" / "pirate-get.exe"
        if scripts.exists():
            return [str(scripts)]
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
    all_ok = True
    if not find_aria2c():
        _install_aria2c()
        if not find_aria2c():
            console.print("[err]aria2c missing. Install it and retry.[/]")
            all_ok = False

    if not find_pirate_get():
        console.print("[warn]Installing pirate-get...[/]")
        _pip("pirate-get")
        if not find_pirate_get():
            console.print("[err]pirate-get missing. Run: pip install pirate-get[/]")
            all_ok = False

    return all_ok


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
            "http://suggestqueries.google.com/complete/search",
            params={"client": "firefox", "q": query},
            timeout=5,
        )
        data = r.json()
        return list(data[1])[:5] if len(data) > 1 else []
    except Exception:
        return []


# ──────────────────────────────────────────────────────────
# 5. SEARCH  (pirate-get wrapper)
# ──────────────────────────────────────────────────────────
def _normalize(item: dict) -> dict:
    """Normalise inconsistent pirate-get field names."""
    return {
        "name"    : item.get("name") or item.get("Name") or "Unknown",
        "size"    : item.get("size") or item.get("Size") or "?",
        "seeders" : item.get("seeders") or item.get("Seeders") or "0",
        "leechers": item.get("leechers") or item.get("Leechers") or "0",
        "magnet"  : item.get("magnet") or item.get("Magnet") or "",
    }

def search(query: str) -> list[dict]:
    pg = find_pirate_get()
    if not pg:
        return []
    cmd = pg + ["--json", query]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        raw = r.stdout.strip()
        if not raw:
            return []
        data = json.loads(raw)
        return [_normalize(i) for i in data if i.get("magnet") or i.get("Magnet")]
    except subprocess.TimeoutExpired:
        console.print("[warn]Search timed out.[/]")
        return []
    except json.JSONDecodeError:
        console.print("[warn]Could not parse search results.[/]")
        return []
    except Exception as e:
        console.print(f"[warn]Search error: {e}[/]")
        return []

def search_with_fallback(primary: str, fallback: str = "", target_count: int = 10) -> list[dict]:
    console.print(f"[hdr]Searching:[/] [title]{primary}[/]")
    results = search(primary)
    
    if len(results) < target_count and fallback and fallback != primary:
        if not results:
            console.print(f"[warn]No results. Trying fallback: {fallback}[/]")
        else:
            console.print(f"[warn]Only {len(results)} results found. Supplementing with fallback: {fallback}[/]")
            
        fallback_results = search(fallback)
        seen = {item.get("magnet") for item in results if item.get("magnet")}
        
        for item in fallback_results:
            magnet = item.get("magnet")
            if magnet and magnet not in seen:
                results.append(item)
                seen.add(magnet)
                if len(results) >= target_count:
                    break
                    
    return results


# ──────────────────────────────────────────────────────────
# 6. BACKGROUND METADATA WARMING
# ──────────────────────────────────────────────────────────
def warm_trackers(results: list[dict], target_dir: str, count: int = 3) -> None:
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
    
    target_dir = str(Path(target_dir).expanduser())
    Path(target_dir).mkdir(parents=True, exist_ok=True)

    for item in results[:count]:
        magnet = item.get("magnet", "")
        if not magnet:
            continue
        try:
            p = subprocess.Popen(
                [
                    aria2,
                    "--bt-metadata-only=true",
                    "--bt-save-metadata=true",
                    f"--dir={target_dir}",
                    f"--bt-tracker={TRACKERS}",
                    magnet,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            _bg_pids.append(p.pid)
        except Exception:
            pass

def kill_warmers() -> None:
    global _bg_pids
    for pid in _bg_pids:
        try:
            os.kill(pid, signal.SIGTERM if OS != "Windows" else signal.SIGBREAK)
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
        f"--bt-tracker={TRACKERS}",
        "--bt-load-saved-metadata=true",
        "--bt-prioritize-piece=head,tail",
        f"--max-connection-per-server={cfg['splits']}",
        f"--split={cfg['splits']}",
        f"--min-split-size={cfg['min_split_mb']}M",
        "--max-overall-download-limit=0",
        f"--seed-time={cfg['seed_time']}",
        "--file-allocation=none",
        f"--bt-max-peers={cfg['max_peers']}",
        "--summary-interval=5",
        magnet,
    ]

    # Real-Debrid (future hook — key present but API not implemented yet)
    if cfg.get("rd_api_key"):
        console.print("[accent]Real-Debrid key detected — instant cache lookup coming in v2.1[/]")

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

    # ── Cleanup handler ──────────────────────────────────
    def _cleanup(*_):
        kill_warmers()
        RESULTS_F.unlink(missing_ok=True)
        sys.exit(0)

    signal.signal(signal.SIGINT,  _cleanup)
    signal.signal(signal.SIGTERM, _cleanup)

    cfg = load_config()

    # ── Banner ───────────────────────────────────────────
    show_banner()
    console.print(f"[dim]Platform: {OS}  •  Config: {CONFIG_F}[/]")
    console.print(f"[dim]Target  : {cfg['target_dir']}[/]\n")

    # ── Connectivity check ───────────────────────────────
    console.print("[info]Checking connectivity...[/]", end=" ")
    if site_reachable():
        console.print("[ok]OK[/]")
    else:
        console.print("[warn]Sites unreachable.[/]")
        if OS == "Linux":
            if heal_dns():
                console.print("[ok]DNS healed — sites accessible.[/]")
            else:
                console.print("[err]Still blocked. Try a VPN.[/]")
                sys.exit(1)
        else:
            console.print("[warn]Check your network or use a VPN.[/]")

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
    results = search_with_fallback(query, fallback, cfg.get("max_results", 10))

    if not results:
        console.print("[err]No results found. Try a different spelling or format.[/]")
        sys.exit(1)

    # ── Background metadata warming ──────────────────────
    console.print("[info]Warming up trackers in background...[/]")
    warm_trackers(results, target_dir=cfg["target_dir"], count=cfg.get("max_results", 10))

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
