"""
N3RAH BOOK — Web Application Launcher
Starts the Flask Web Application server and opens your browser automatically.
"""

import os
import sys
import webbrowser
import threading
import time
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from webapp.app import app
from database.db_manager import db

def open_browser(port):
    time.sleep(1.2)
    url = f"http://127.0.0.1:{port}/login"
    print(f"[LAUNCH] Opening browser at: {url}")
    try:
        webbrowser.open(url)
    except Exception as ex:
        print(f"[WARN] Could not auto-launch browser ({ex}). Please visit: {url}")

def main():
    port = int(os.environ.get("PORT", 5000))
    backend_name = "Cloud PostgreSQL" if db.cloud_mode else "Local SQLite"

    print("=" * 65)
    print("   N3RAH BOOK — ENTERPRISE BILLING & INVENTORY WEB APPLICATION")
    print("=" * 65)
    print(f"  * Web URL:      http://127.0.0.1:{port}")
    print(f"  * Database:     {backend_name}")
    print(f"  * Admin Login:  Username: admin | Password: (Your configured password)")
    print("=" * 65)
    print("  Press Ctrl+C in this terminal window to stop the server.")
    print("=" * 65 + "\n")

    # Start browser auto-opener in background thread
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    # Start Flask Web Server
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)

if __name__ == "__main__":
    main()
