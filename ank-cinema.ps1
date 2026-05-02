# =============================================================
#  ANK-CINEMA ARCHITECT v2.0 — Windows PowerShell Launcher
#  Run: .\ank-cinema.ps1
#  Requires: Python 3.8+ in PATH
# =============================================================

$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$CoreScript = Join-Path $ScriptDir "ank_cinema_core.py"

# ── Find Python ──────────────────────────────────────────
$python = $null
foreach ($candidate in @("python", "python3", "py")) {
    try {
        $ver = & $candidate -c "import sys; print(sys.version_info >= (3,8))" 2>$null
        if ($ver -eq "True") { $python = $candidate; break }
    } catch {}
}

if (-not $python) {
    Write-Host "❌  Python 3.8+ is required." -ForegroundColor Red
    Write-Host "    Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "    Or via winget: winget install Python.Python.3" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# ── Launch core ──────────────────────────────────────────
& $python $CoreScript @args
