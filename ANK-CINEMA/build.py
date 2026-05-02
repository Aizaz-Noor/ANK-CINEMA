import os
import sys
import shutil
import platform
import subprocess
import requests
import zipfile
import tarfile
from pathlib import Path

# ──────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────
APP_NAME = "ANK-CINEMA"
VERSION  = "3.0.0"
OS       = platform.system()
ROOT     = Path(__file__).parent.resolve()
BIN_DIR  = ROOT / "bin"
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build"

# Official aria2c release versions
ARIA2_VER = "1.37.0"
ARIA2_URLS = {
    "Windows": f"https://github.com/aria2/aria2/releases/download/release-{ARIA2_VER}/aria2-{ARIA2_VER}-win-64bit-build1.zip",
    "Linux":   f"https://github.com/aria2/aria2/releases/download/release-{ARIA2_VER}/aria2-{ARIA2_VER}-aarch64-linux-android-build1.tar.bz2", # Placeholder for x86_64
    "Darwin":  f"https://github.com/aria2/aria2/releases/download/release-{ARIA2_VER}/aria2-{ARIA2_VER}-osx-64bit-build1.tar.bz2"
}

def setup_binaries():
    """Download and prepare aria2c binaries for bundling."""
    BIN_DIR.mkdir(exist_ok=True)
    exe_name = "aria2c.exe" if OS == "Windows" else "aria2c"
    target_exe = BIN_DIR / exe_name
    
    if target_exe.exists():
        print(f"[build] {exe_name} already exists in bin/")
        return True

    print(f"[build] Downloading aria2c engine v{ARIA2_VER} for {OS}...")
    url = ARIA2_URLS.get(OS)
    if not url:
        print(f"[err] No auto-download URL for {OS}. Place aria2c in bin/ manually.")
        return False

    tmp_file = ROOT / "temp_aria2.archive"
    try:
        r = requests.get(url, stream=True)
        with open(tmp_file, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
        
        # Extract
        print("[build] Extracting...")
        if url.endswith(".zip"):
            with zipfile.ZipFile(tmp_file, 'r') as z:
                # Find the exe in the zip
                for name in z.namelist():
                    if name.endswith("aria2c.exe"):
                        with z.open(name) as source, open(target_exe, 'wb') as target:
                            shutil.copyfileobj(source, target)
        else:
            with tarfile.open(tmp_file, "r:bz2") as tar:
                 for member in tar.getmembers():
                    if member.name.endswith("aria2c"):
                        member.name = os.path.basename(member.name)
                        tar.extract(member, path=BIN_DIR)
        
        os.chmod(target_exe, 0o755)
        print(f"[build] Engine ready: {target_exe}")
    except Exception as e:
        print(f"[err] Failed to setup binaries: {e}")
        return False
    finally:
        if tmp_file.exists(): os.remove(tmp_file)
    return True

def run_build():
    """Compile using PyInstaller."""
    print(f"\n[build] STARTING COMPILATION: {APP_NAME} v{VERSION}")
    
    # Ensure dependencies are installed for building
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller", "requests", "rich"], check=True)
    
    core_script = ROOT / "ank_cinema_core.py"
    if not core_script.exists():
        print("[err] ank_cinema_core.py not found!")
        return

    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",
        "--name", APP_NAME,
        "--clean",
        "--add-data", f"bin{os.pathsep}bin",
        str(core_script)
    ]
    
    # Hide console on Windows for "real app" feel? 
    # Actually for CLI apps we MUST show the console.
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n[ok] BUILD COMPLETE! Check the 'dist' folder for your binary.")
        print(f"Location: {DIST_DIR / (APP_NAME + ('.exe' if OS == 'Windows' else ''))}")
    except Exception as e:
        print(f"[err] Compilation failed: {e}")

if __name__ == "__main__":
    if setup_binaries():
        run_build()
