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

:: -- Find Python -----------------------------------------------------
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

:: -- First-time setup / virtualenv creation ---------------------------
if not exist "%VENV_DIR%\Scripts\python.exe" if not exist "%VENV_DIR%\bin\python.exe" (
    echo.
    echo  [INFO] First-time setup: creating portable virtual environment.
    echo  [INFO] Required Python packages will be installed automatically.
    "%PYTHON%" -m venv "%VENV_DIR%" >nul 2>&1
    if errorlevel 1 (
        echo.
        echo  [ERR] Virtual environment creation failed.
        echo  Make sure Python 3.8+ is installed and available on the PATH.
        pause
        exit /b 1
    )
)

:: -- Resolve venv Python executable ----------------------------------
if exist "%VENV_DIR%\Scripts\python.exe" (
    set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
) else if exist "%VENV_DIR%\bin\python.exe" (
    set "VENV_PY=%VENV_DIR%\bin\python.exe"
) else (
    set "VENV_PY=%PYTHON%"
)

:: -- Install required packages if needed ------------------------------
if defined VENV_PY (
    "%VENV_PY%" -m pip install --quiet requests rich >nul 2>&1
) else (
    echo.
    echo  [ERR] Could not resolve a Python interpreter.
    pause
    exit /b 1
)

:: -- Mark setup as complete only after successful setup ----------------
if not exist "%READY_FLAG%" (
    echo installed > "%READY_FLAG%"
)

:: -- Add project dir + venv scripts to PATH ---------------------------
set "VENV_BIN="
if exist "%VENV_DIR%\Scripts" set "VENV_BIN=%VENV_DIR%\Scripts"
if not defined VENV_BIN (
    if exist "%VENV_DIR%\bin" set "VENV_BIN=%VENV_DIR%\bin"
)
if exist "%SCRIPT_DIR%bin" (
    set "PATH=%SCRIPT_DIR%bin;%PATH%"
)
set "PATH=%SCRIPT_DIR%;%VENV_BIN%;%PATH%"
set "PYTHONIOENCODING=utf-8"

if not exist "%CORE%" (
    echo.
    echo  [ERR] Core application file not found: %CORE%
    pause
    exit /b 1
)

echo Starting ANK-Cinema...
"%VENV_PY%" "%CORE%"

if errorlevel 1 (
    echo.
    echo  [!!] ANK-Cinema exited with an error.
    echo  [!!] Delete the file ".installed" and re-run this bat to reinstall.
    echo.
    pause
)
endlocal
