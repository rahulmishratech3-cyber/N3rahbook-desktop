"""
User Login Session Management Service
Persists login session with a 24-hour expiration (86,400 seconds).
"""

import os
import json
import time
from pathlib import Path
from config import BASE_DIR

SESSION_FILE = Path(BASE_DIR) / ".session.json" if BASE_DIR else Path(".session.json")
SESSION_DURATION_SECONDS = 24 * 60 * 60  # 24 Hours


def save_session(user):
    """
    Saves the user session details along with current timestamp and 24-hour expiry timestamp.
    """
    now = time.time()
    session_data = {
        'user': user,
        'login_time': now,
        'expiry_time': now + SESSION_DURATION_SECONDS
    }
    try:
        with open(SESSION_FILE, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2)
        return True
    except Exception as ex:
        print(f"Failed to save session: {ex}")
        return False


def get_active_session():
    """
    Checks if a valid, non-expired session exists.
    Returns user dict if valid (< 24 hours old), or None if expired/missing.
    """
    if not SESSION_FILE.exists():
        return None

    try:
        with open(SESSION_FILE, 'r', encoding='utf-8') as f:
            session_data = json.load(f)

        expiry_time = session_data.get('expiry_time', 0)
        now = time.time()

        if now < expiry_time:
            return session_data.get('user')
        else:
            # Session expired
            clear_session()
            return None
    except Exception as ex:
        print(f"Error reading session file: {ex}")
        clear_session()
        return None


def clear_session():
    """
    Clears active session file on logout or session expiration.
    """
    try:
        if SESSION_FILE.exists():
            os.remove(SESSION_FILE)
    except Exception as ex:
        print(f"Failed to remove session file: {ex}")
