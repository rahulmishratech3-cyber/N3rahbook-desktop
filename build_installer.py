"""
Build Single-File Windows Setup Installer (N3RAH_BOOK_Setup.exe)
Bundles application data and setup_wizard into a single executable installer wizard.
"""

import os
import sys
import shutil
import subprocess

def build():
    print("==================================================")
    print("Building N3RAH BOOK Standalone Setup Installer")
    print("==================================================")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(base_dir, "dist")
    payload_dir = os.path.join(dist_dir, "N3RAH_BOOK")

    if not os.path.exists(payload_dir):
        print(f"Error: Executable bundle not found at {payload_dir}. Please run build_exe.py first.")
        sys.exit(1)

    payload_zip = os.path.join(base_dir, "app_payload.zip")
    print(f"Creating payload archive from {payload_dir}...")
    
    shutil.make_archive(os.path.join(base_dir, "app_payload"), 'zip', payload_dir)
    print(f"Payload archive created at {payload_zip}")

    # Build Setup Installer .exe
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name=N3RAH_BOOK_Setup",
        f"--add-data={payload_zip};.",
        f"--icon={os.path.join(base_dir, 'assets', 'logo_icon.png')}",
        "setup_wizard.py"
    ]

    print("Compiling N3RAH_BOOK_Setup.exe installer...")
    res = subprocess.run(cmd)

    # Clean up temporary zip
    if os.path.exists(payload_zip):
        os.remove(payload_zip)

    if res.returncode == 0:
        installer_exe = os.path.join(dist_dir, "N3RAH_BOOK_Setup.exe")
        print("\n==================================================")
        print("[SUCCESS] Standalone Windows Setup Installer Created!")
        print(f"Single Setup Installer Executable: {installer_exe}")
        print("==================================================")
    else:
        print("\n[ERROR] Failed to compile Setup Installer!")

if __name__ == "__main__":
    build()
