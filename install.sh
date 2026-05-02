#!/bin/bash
# ============================================================
#  ANK-CINEMA ARCHITECT v2.0 — Linux / macOS Installer
#  Usage: bash install.sh
# ============================================================

set -e
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

ok()   { echo -e "${GREEN}✅  $*${NC}"; }
warn() { echo -e "${YELLOW}⚠️   $*${NC}"; }
err()  { echo -e "${RED}❌  $*${NC}"; exit 1; }
step() { echo -e "\n${YELLOW}──  $*${NC}"; }

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════╗"
echo -e "║      ANK-CINEMA ARCHITECT v2.0  Installer       ║"
echo -e "╚══════════════════════════════════════════════════╝${NC}"
echo ""

# ── 1. Python ────────────────────────────────────────────
step "Checking Python 3.8+"
PYTHON=""
for c in python3 python python3.12 python3.11 python3.10; do
    if command -v "$c" &>/dev/null; then
        ver=$("$c" -c 'import sys; print(sys.version_info >= (3,8))' 2>/dev/null)
        [ "$ver" = "True" ] && PYTHON="$c" && break
    fi
done

if [ -z "$PYTHON" ]; then
    warn "Python 3.8+ not found. Attempting install..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get update -qq && sudo apt-get install -y python3 python3-pip
        PYTHON=python3
    elif command -v brew &>/dev/null; then
        brew install python3
        PYTHON=python3
    else
        err "Install Python 3.8+ manually: https://python.org/downloads"
    fi
fi
ok "Python found: $($PYTHON --version)"

# ── 2. pip dependencies ──────────────────────────────────
step "Installing Python dependencies"
$PYTHON -m pip install --quiet --break-system-packages \
    requests rich pirate-get 2>/dev/null || \
$PYTHON -m pip install --quiet --user \
    requests rich pirate-get
ok "Python packages installed"

# ── 3. aria2c ────────────────────────────────────────────
step "Checking aria2c"
if command -v aria2c &>/dev/null; then
    ok "aria2c found: $(aria2c --version | head -1)"
else
    warn "aria2c not found. Installing..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get install -y aria2
    elif command -v brew &>/dev/null; then
        brew install aria2
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm aria2
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y aria2
    else
        err "Install aria2c manually: https://github.com/aria2/aria2/releases"
    fi
    ok "aria2c installed"
fi

# ── 4. Make scripts executable ───────────────────────────
step "Setting permissions"
chmod +x "$REPO_DIR/ank-cinema.sh"
chmod +x "$REPO_DIR/ank_cinema_core.py"
ok "Permissions set"

# ── 5. Optional: global symlink ──────────────────────────
step "Creating global command (optional)"
LINK="/usr/local/bin/ank-cinema"
if [ -w /usr/local/bin ]; then
    ln -sf "$REPO_DIR/ank-cinema.sh" "$LINK"
    ok "Global command created: ank-cinema"
elif command -v sudo &>/dev/null; then
    sudo ln -sf "$REPO_DIR/ank-cinema.sh" "$LINK" 2>/dev/null && \
        ok "Global command created: ank-cinema" || \
        warn "Could not create global command (skipping)"
else
    warn "Add this to your shell config to use 'ank-cinema' globally:"
    echo "    alias ank-cinema='bash $REPO_DIR/ank-cinema.sh'"
fi

# ── 6. Create default config ─────────────────────────────
step "Initialising config"
mkdir -p ~/.ank-cinema
if [ ! -f ~/.ank-cinema/config.json ]; then
    $PYTHON "$REPO_DIR/ank_cinema_core.py" --init-config 2>/dev/null || true
    # Fallback: write default manually
    cat > ~/.ank-cinema/config.json <<'JSON'
{
  "target_dir": "~/Movies",
  "rd_api_key": "",
  "max_results": 10,
  "splits": 16,
  "max_peers": 200,
  "seed_time": 0,
  "min_split_mb": 1
}
JSON
    ok "Config created at ~/.ank-cinema/config.json"
else
    ok "Config already exists"
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════╗"
echo -e "║          Installation complete! 🎬              ║"
echo -e "║                                                  ║"
echo -e "║  Run:  ank-cinema             (if global)        ║"
echo -e "║  Or:   bash ank-cinema.sh     (local)            ║"
echo -e "╚══════════════════════════════════════════════════╝${NC}"
echo ""
