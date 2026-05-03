@echo off
@echo off
:: ANK-CINEMA Launcher
setlocal EnableDelayedExpansion

:: Force UTF-8 for UI
chcp 65001 >nul 2>&1

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%.venv"
set "CORE=%SCRIPT_DIR%ank_cinema_core.py"
set "ARIA2=%SCRIPT_DIR%bin\aria2c.exe"
set "READY_FLAG=%SCRIPT_DIR%.installed"

:: ── Find Python ──────────────────────────────────────────
set "PYTHON="
for %%c in (python python3 py) do (
    if not defined PYTHON (
        %%c --version >nul 2>&1 && set "PYTHON=%%c"
    )
)

if not defined PYTHON (
    echo.
    echo  [!!] Python not found.
    echo  [!!] Opening download page...
    start https://www.python.org/downloads/
    echo.
    echo  After installing Python, close this window and
    echo  double-click ANK-CINEMA.bat again.
    echo.
    pause
    exit /b 1
)

:: ── First-time setup ─────────────────────────────────────
if not exist "%READY_FLAG%" (
    echo.
    echo  +------------------------------------------+
    echo  ^|  ANK-CINEMA — First-Time Setup           ^|
    echo  ^|  This runs once. Future starts are       ^|
    echo  ^|  instant.                                ^|
    echo  +------------------------------------------+
    echo.

    :: Run the PowerShell installer (sets ExecutionPolicy for
    :: itself only — does NOT change your system policy)
    powershell -NoProfile -ExecutionPolicy Bypass -File "%INSTALLER%"

    if errorlevel 1 (
        echo.
        echo  [ERR] Setup failed. See messages above.
        pause
        exit /b 1
    )

    :: Mark as installed
    echo installed > "%READY_FLAG%"
    echo.
    echo  [OK] Setup complete! Launching now...
    echo.
    timeout /t 2 /nobreak >nul
)

:: ── Resolve venv Python (Scripts\ or bin\) ───────────────
set "VENV_PY="
if exist "%VENV_DIR%\Scripts\python.exe" set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
if not defined VENV_PY (
    if exist "%VENV_DIR%\bin\python.exe" set "VENV_PY=%VENV_DIR%\bin\python.exe"
)

:: Fall back to system Python if venv somehow missing
if not defined VENV_PY set "VENV_PY=%PYTHON%"

:: ── Add project dir + venv scripts to PATH ───────────────
:: This makes bundled aria2c.exe and pirate-get visible
set "VENV_BIN="
if exist "%VENV_DIR%\Scripts" set "VENV_BIN=%VENV_DIR%\Scripts"
if not defined VENV_BIN (
    if exist "%VENV_DIR%\bin" set "VENV_BIN=%VENV_DIR%\bin"
)
set "PATH=%SCRIPT_DIR%;%VENV_BIN%;%PATH%"

:: ── Set UTF-8 for Python too ─────────────────────────────
set "PYTHONIOENCODING=utf-8"

if not exist "!VENV_DIR!" (
    echo Starting first-time setup...
    python -m venv "!VENV_DIR!" >nul 2>&1
    "!VENV_DIR!\Scripts\pip" install --quiet requests rich >nul 2>&1
    echo Setup complete.
    echo. > "!READY_FLAG!"
)

:: Launch
echo Starting ANK-Cinema...
"!VENV_DIR!\Scripts\python" "!CORE!"

:: Keep window open if there was an error
if errorlevel 1 (
    echo.
    echo  [!!] ANK-Cinema exited with an error.
    echo  [!!] Delete the file ".installed" and re-run
    echo  [!!] this bat to reinstall.
    echo.
    pause
)
endlocal
