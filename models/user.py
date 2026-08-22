"""
User Account Model and Password Authentication Service
"""

import hashlib
from database.db_manager import db

class UserModel:
    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    @staticmethod
    def authenticate(username, password):
        user = db.fetch_one("SELECT * FROM users WHERE username = ? AND status = 'Active'", (username.strip(),))
        if not user:
            return None

        hashed_input = UserModel.hash_password(password)
        if user['password_hash'] == hashed_input:
            return user
        return None

    @staticmethod
    def create_user(username, password, full_name="System Admin", role="Admin", status="Active"):
        pass_hash = UserModel.hash_password(password)
        sql = "INSERT OR IGNORE INTO users (username, password_hash, full_name, role, status) VALUES (?, ?, ?, ?, ?)"
        return db.execute_query(sql, (username.strip(), pass_hash, full_name, role, status))

    @staticmethod
    def update_user(user_id, data, password=None):
        if password and password.strip():
            pass_hash = UserModel.hash_password(password)
            sql = "UPDATE users SET username = ?, full_name = ?, role = ?, status = ?, password_hash = ? WHERE id = ?"
            db.execute_query(sql, (data['username'].strip(), data['full_name'].strip(), data['role'], data['status'], pass_hash, user_id))
        else:
            sql = "UPDATE users SET username = ?, full_name = ?, role = ?, status = ? WHERE id = ?"
            db.execute_query(sql, (data['username'].strip(), data['full_name'].strip(), data['role'], data['status'], user_id))

    @staticmethod
    def delete_user(user_id):
        db.execute_query("DELETE FROM users WHERE id = ?", (user_id,))

    @staticmethod
    def get_by_id(user_id):
        return db.fetch_one("SELECT id, username, full_name, role, status, created_at FROM users WHERE id = ?", (user_id,))

    @staticmethod
    def get_all():
        return db.fetch_all("SELECT id, username, full_name, role, status, created_at FROM users ORDER BY id DESC")
