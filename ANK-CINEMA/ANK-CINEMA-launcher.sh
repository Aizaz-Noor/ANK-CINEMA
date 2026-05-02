#!/usr/bin/env bash
# ============================================================
#  ANK-CINEMA ARCHITECT v3.0 — One-Click Launcher
#  Linux (.desktop) · macOS (.command)
# ============================================================

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

# ── First-time setup ─────────────────────────────────────
if [ ! -f "$READY_FLAG" ]; then
    echo ""
    echo "  +------------------------------------------+"
    echo "  |  ANK-CINEMA — First-Time Setup           |"
    echo "  |  This runs once. Future starts instant.  |"
    echo "  +------------------------------------------+"
  # ── Setup Environment ──────────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    echo "[setup] Initializing ANK-Cinema v3.0..."
    echo "[setup] Creating private environment (this only happens once)..."
    "$PYTHON" -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "[err] Python not found or venv failed. Please install Python 3.10+"
        exit 1
    fi
    echo "[setup] Installing core dependencies..."
    "$VENV_DIR/bin/pip" install --quiet requests rich
    echo "[setup] Setup complete!"
    touch "$READY_FLAG"
fi
fi

# ── Launch ───────────────────────────────────────────────
echo "[launch] Starting ANK-Cinema Architect..."
"$VENV_DIR/bin/python" "$CORE"
