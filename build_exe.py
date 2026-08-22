"""
PyInstaller Standalone Executable Build Script
Packages N3RAH BOOK into a self-contained production .exe distribution folder with current database.
"""

import os
import sys
import shutil
import subprocess

def build():
    print("==================================================")
    print("N3RAH BOOK - Production Executable Build Engine")
    print("==================================================")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(base_dir, "dist")
    build_dir = os.path.join(base_dir, "build")

    # 1. Clean previous build & dist folders
    print("Cleaning previous build and dist directories...")
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir, ignore_errors=True)
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir, ignore_errors=True)

    # 2. PyInstaller Build Command
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=N3RAH_BOOK",
        "--add-data=assets;assets",
        "--add-data=config.py;.",
        "--add-data=inventory_system.db;.",
        f"--icon={os.path.join(base_dir, 'assets', 'logo_icon.png')}",
        "main.py"
    ]

    print("Building executable bundle...")
    res = subprocess.run(cmd)

    if res.returncode == 0:
        target_bundle = os.path.join(dist_dir, "N3RAH_BOOK")
        
        # Copy latest inventory_system.db and assets directly into target bundle root
        db_src = os.path.join(base_dir, "inventory_system.db")
        db_dst = os.path.join(target_bundle, "inventory_system.db")
        if os.path.exists(db_src):
            shutil.copy2(db_src, db_dst)
            print(f"[OK] Live database copied to bundle: {db_dst}")

        assets_src = os.path.join(base_dir, "assets")
        assets_dst = os.path.join(target_bundle, "assets")
        if os.path.exists(assets_src) and not os.path.exists(assets_dst):
            shutil.copytree(assets_src, assets_dst)
            print(f"[OK] Assets copied to bundle: {assets_dst}")

        print("\n==================================================")
        print("[SUCCESS] Build Completed Successfully!")
        print(f"Output Bundle Directory: {target_bundle}")
        print(f"Main Executable: {os.path.join(target_bundle, 'N3RAH_BOOK.exe')}")
        print("==================================================")
    else:
        print("\n[ERROR] Build Failed! Check output logs above.")

if __name__ == "__main__":
    build()
