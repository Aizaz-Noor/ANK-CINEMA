#!/bin/bash
# ============================================================
#  ANK-CINEMA ARCHITECT v2.0 — macOS One-Click Launcher
#  Double-click this file in Finder. Terminal opens and
#  the tool installs + launches automatically.
#
#  First run : installs everything, then launches
#  Every run : launches instantly
# ============================================================

# cd to script's own folder (Finder opens .command from ~)
cd "$(dirname "$0")"

READY_FLAG=".installed"
INSTALLER="./install.sh"
CORE="./ank_cinema_core.py"

# ── Find Python ──────────────────────────────────────────
PYTHON=""
for c in python3 python python3.12 python3.11 python3.10; do
    if command -v "$c" &>/dev/null; then
        ver=$("$c" -c 'import sys; print(sys.version_info >= (3,8))' 2>/dev/null)
        [ "$ver" = "True" ] && PYTHON="$c" && break
    fi
done

if [ -z "$PYTHON" ]; then
    echo ""
    echo "  [!!] Python 3.8+ not found."
    echo "  [!!] Install via Homebrew:  brew install python3"
    echo "  [!!] Or download from:      https://python.org/downloads"
    echo ""
    read -p "Press Enter to open the download page..."
    open "https://www.python.org/downloads/"
    exit 1
fi

export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"

# ── First-time setup ─────────────────────────────────────
if [ ! -f "$READY_FLAG" ]; then
    echo ""
    echo "  +------------------------------------------+"
    echo "  |  ANK-CINEMA — First-Time Setup           |"
    echo "  |  This runs once. Future starts instant.  |"
    echo "  +------------------------------------------+"
    echo ""
    bash "$INSTALLER"
    if [ $? -ne 0 ]; then
        echo ""
        echo "  [ERR] Setup failed. See messages above."
        read -p "Press Enter to exit..."
        exit 1
    fi
    echo "installed" > "$READY_FLAG"
    echo ""
    echo "  [OK] Setup complete! Launching now..."
    sleep 1
fi

# ── Launch ───────────────────────────────────────────────
"$PYTHON" "$CORE"
