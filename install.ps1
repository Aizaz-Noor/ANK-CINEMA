# =============================================================
#  ANK-CINEMA ARCHITECT v2.0 — Windows Installer
#  Run in PowerShell (Admin recommended for global install):
#      Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
#      .\install.ps1
# =============================================================

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Ok($msg)   { Write-Host "✅  $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "⚠️   $msg" -ForegroundColor Yellow }
function Step($msg) { Write-Host "`n──  $msg" -ForegroundColor Cyan }
function Err($msg)  { Write-Host "❌  $msg" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║      ANK-CINEMA ARCHITECT v2.0  Installer       ║" -ForegroundColor Green
Write-Host "║               Windows Edition                   ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

# ── 1. Python ────────────────────────────────────────────
Step "Checking Python 3.8+"
$python = $null
foreach ($c in @("python", "python3", "py")) {
    try {
        $v = & $c -c "import sys; print(sys.version_info >= (3,8))" 2>$null
        if ($v -eq "True") { $python = $c; break }
    } catch {}
}

if (-not $python) {
    Warn "Python not found. Attempting install via winget..."
    try {
        winget install Python.Python.3.12 --silent --accept-package-agreements
        $python = "python"
        Ok "Python installed"
    } catch {
        Err "Install Python manually: https://www.python.org/downloads"
    }
} else {
    $pyVer = & $python --version
    Ok "Python found: $pyVer"
}

# ── 2. pip dependencies ──────────────────────────────────
Step "Installing Python dependencies"
& $python -m pip install --quiet requests rich pirate-get
Ok "Python packages installed"

# ── 3. aria2c ────────────────────────────────────────────
Step "Checking aria2c"
$aria2Found = $false
foreach ($c in @("aria2c", "aria2c.exe")) {
    if (Get-Command $c -ErrorAction SilentlyContinue) {
        $aria2Found = $true; break
    }
}

if (-not $aria2Found) {
    Warn "aria2c not found. Trying package managers..."
    $installed = $false

    foreach ($mgr in @(
        @{ name="winget"; cmd=@("winget","install","-e","--id","aria2.aria2","--silent","--accept-package-agreements") },
        @{ name="scoop";  cmd=@("scoop","install","aria2") },
        @{ name="choco";  cmd=@("choco","install","aria2","-y") }
    )) {
        if (Get-Command $mgr.name -ErrorAction SilentlyContinue) {
            & $mgr.cmd[0] $mgr.cmd[1..($mgr.cmd.Length-1)]
            $installed = $true
            break
        }
    }

    if (-not $installed) {
        Warn "No package manager found."
        Write-Host "    Download aria2c from: https://github.com/aria2/aria2/releases" -ForegroundColor Yellow
        Write-Host "    Extract aria2c.exe and add its folder to your PATH." -ForegroundColor Yellow
    } else {
        Ok "aria2c installed"
    }
} else {
    Ok "aria2c found"
}

# ── 4. Default config ────────────────────────────────────
Step "Initialising config"
$cfgDir = Join-Path $env:USERPROFILE ".ank-cinema"
$cfgFile = Join-Path $cfgDir "config.json"
if (-not (Test-Path $cfgFile)) {
    New-Item -ItemType Directory -Force -Path $cfgDir | Out-Null
    $moviesPath = [System.IO.Path]::Combine($env:USERPROFILE, "Movies")
    $cfg = @{
        target_dir   = $moviesPath
        rd_api_key   = ""
        max_results  = 10
        splits       = 16
        max_peers    = 200
        seed_time    = 0
        min_split_mb = 1
    } | ConvertTo-Json -Depth 3
    $cfg | Out-File -FilePath $cfgFile -Encoding UTF8
    Ok "Config created at $cfgFile"
} else {
    Ok "Config already exists"
}

# ── 5. Optional: PowerShell profile alias ────────────────
Step "Creating shell alias (optional)"
$profileDir = Split-Path $PROFILE -Parent
if (-not (Test-Path $profileDir)) { New-Item -ItemType Directory -Force $profileDir | Out-Null }
$alias = "`nfunction ank-cinema { & '$python' '$ScriptDir\ank_cinema_core.py' `$args }"
if (-not (Test-Path $PROFILE) -or -not (Select-String -Path $PROFILE -Pattern "ank-cinema" -Quiet)) {
    Add-Content -Path $PROFILE -Value $alias
    Ok "Added 'ank-cinema' function to PowerShell profile"
} else {
    Ok "Shell alias already exists"
}

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║           Installation complete! 🎬             ║" -ForegroundColor Green
Write-Host "║                                                  ║" -ForegroundColor Green
Write-Host "║  Run:  .\ank-cinema.ps1       (local)           ║" -ForegroundColor Green
Write-Host "║  Or:   ank-cinema             (after new shell) ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
