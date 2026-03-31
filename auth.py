# auth.py - Login, Signup, Logout system using SQLite

import sqlite3
import hashlib
import os
from datetime import datetime

DB_PATH = "users.db"

def init_db():
    """Create users table if not exists"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def signup(username: str, password: str) -> dict:
    """Register a new user"""
    if len(username.strip()) < 3:
        return {"success": False, "message": "Username must be at least 3 characters!"}
    if len(password) < 6:
        return {"success": False, "message": "Password must be at least 6 characters!"}

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)",
            (username.strip().lower(), hash_password(password), datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        conn.commit()
        conn.close()
        return {"success": True, "message": f"Account created! Welcome, {username}!"}
    except sqlite3.IntegrityError:
        return {"success": False, "message": "Username already exists! Try another one."}
    except Exception as e:
        return {"success": False, "message": str(e)}

def login(username: str, password: str) -> dict:
    """Login with username and password"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "SELECT id, username FROM users WHERE username=? AND password=?",
            (username.strip().lower(), hash_password(password))
        )
        user = c.fetchone()
        conn.close()

        if user:
            return {"success": True, "user_id": user[0], "username": user[1]}
        else:
            return {"success": False, "message": "Wrong username or password!"}
    except Exception as e:
        return {"success": False, "message": str(e)}
