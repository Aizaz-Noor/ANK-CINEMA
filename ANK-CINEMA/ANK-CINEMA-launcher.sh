#!/usr/bin/env bash
# ANK-CINEMA Launcher

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CORE="$SCRIPT_DIR/ank_cinema_core.py"
BIN_DIR="$SCRIPT_DIR/bin"
READY_FLAG="$SCRIPT_DIR/.installed"

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
    echo "  [!!] Install with:  sudo apt install python3"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

export PATH="$HOME/.local/bin:$PATH"

VENV_DIR="$SCRIPT_DIR/.venv"

# ── First-time setup ─────────────────────────────────────
if [ ! -f "$READY_FLAG" ]; then
    echo "Starting first-time setup..."
    "$PYTHON" -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install --quiet requests rich
    touch "$READY_FLAG"
fi

# Launch
echo "Starting ANK-Cinema..."
"$VENV_DIR/bin/python" "$CORE"
