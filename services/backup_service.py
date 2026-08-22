"""
Cloud & Server Data Backup Service
Handles local database snapshots, HTTP POST uploads to custom remote servers, and sync directory copies.
"""

import os
import sys
import json
import shutil
import time
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path
from config import BASE_DIR, DB_PATH, EXPORTS_DIR

BACKUPS_DIR = EXPORTS_DIR / "backups"
BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = BASE_DIR / "backup_config.json"


def get_backup_config():
    """
    Retrieves current backup configuration settings.
    """
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass

    return {
        'server_url': '',
        'api_token': '',
        'sync_folder': '',
        'auto_backup_on_exit': True,
        'last_backup_time': 'Never',
        'last_backup_status': 'No backup performed yet'
    }


def save_backup_config(config):
    """
    Saves backup configuration settings.
    """
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as ex:
        print(f"Failed to save backup config: {ex}")
        return False


def create_local_backup():
    """
    Creates a timestamped snapshot of inventory_system.db in exports/backups/
    """
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database file not found at {DB_PATH}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"inventory_backup_{timestamp}.db"
    backup_filepath = BACKUPS_DIR / backup_filename

    shutil.copy2(DB_PATH, backup_filepath)
    file_size_kb = os.path.getsize(backup_filepath) / 1024.0

    return str(backup_filepath), backup_filename, file_size_kb


def push_to_remote_server(filepath, server_url, api_token=None):
    """
    Uploads backup snapshot to custom remote server URL via HTTP POST multipart form data.
    """
    if not server_url:
        return False, "No server URL provided"

    try:
        boundary = '----WebKitFormBoundary' + datetime.now().strftime("%Y%m%d%H%M%S")
        filename = os.path.basename(filepath)

        with open(filepath, 'rb') as f:
            file_data = f.read()

        body = []
        body.append(f'--{boundary}'.encode('utf-8'))
        body.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode('utf-8'))
        body.append('Content-Type: application/octet-stream\r\n'.encode('utf-8'))
        body.append(file_data)
        body.append(f'--{boundary}--\r\n'.encode('utf-8'))

        payload = b'\r\n'.join(body)

        req = urllib.request.Request(server_url, data=payload, method='POST')
        req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
        req.add_header('User-Agent', 'N3RAH-BOOK-BackupAgent/1.0')

        if api_token:
            req.add_header('Authorization', f'Bearer {api_token}')
            req.add_header('X-API-Key', api_token)

        with urllib.request.urlopen(req, timeout=15) as response:
            res_body = response.read().decode('utf-8', errors='ignore')
            return True, f"Server HTTP {response.status}: Backup uploaded successfully!"
    except Exception as ex:
        return False, f"Server Upload Failed: {str(ex)}"


def copy_to_sync_folder(filepath, destination_folder):
    """
    Copies database snapshot to a local or cloud sync directory (Google Drive / OneDrive / Local folder).
    """
    if not destination_folder or not os.path.exists(destination_folder):
        return False, "Destination folder does not exist"

    try:
        dest_file = os.path.join(destination_folder, os.path.basename(filepath))
        shutil.copy2(filepath, dest_file)
        return True, f"Copied backup to {dest_file}"
    except Exception as ex:
        return False, f"Sync Folder Copy Failed: {str(ex)}"


def run_full_backup():
    """
    Executes local backup creation, optional remote server upload, and optional sync folder copy.
    Returns status dict.
    """
    config = get_backup_config()
    backup_path, backup_name, file_size_kb = create_local_backup()

    status_messages = [f"Local Snapshot created ({file_size_kb:.1f} KB)"]

    # Remote server push if URL configured
    if config.get('server_url'):
        success, msg = push_to_remote_server(backup_path, config['server_url'], config.get('api_token'))
        status_messages.append(msg)

    # Sync folder copy if folder configured
    if config.get('sync_folder'):
        success, msg = copy_to_sync_folder(backup_path, config['sync_folder'])
        status_messages.append(msg)

    now_str = datetime.now().strftime("%d/%m/%Y %I:%M %p")
    full_status_str = " | ".join(status_messages)

    config['last_backup_time'] = now_str
    config['last_backup_status'] = full_status_str
    save_backup_config(config)

    return {
        'timestamp': now_str,
        'filepath': backup_path,
        'filename': backup_name,
        'size_kb': file_size_kb,
        'status': full_status_str
    }
