#!/bin/bash
# ============================================================
#  ANK-CINEMA ARCHITECT v2.0 — Linux / macOS Launcher
#  This script is a thin wrapper around ank_cinema_core.py
#  All logic lives in the Python core for cross-platform use.
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORE="$SCRIPT_DIR/ank_cinema_core.py"

# ── Ensure Python 3.8+ is available ──────────────────────
PYTHON=""
for candidate in python3 python python3.12 python3.11 python3.10; do
    if command -v "$candidate" &>/dev/null; then
        ver=$("$candidate" -c 'import sys; print(sys.version_info >= (3,8))' 2>/dev/null)
        if [ "$ver" = "True" ]; then
            PYTHON="$candidate"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "❌  Python 3.8+ is required."
    echo "    Ubuntu/Debian : sudo apt install python3"
    echo "    macOS         : brew install python3"
    exit 1
fi

# ── Export PATH so pip-installed tools are found ─────────
export PATH="$HOME/.local/bin:$PATH"

# ── Pass all arguments to the Python core ────────────────
exec "$PYTHON" "$CORE" "$@"
