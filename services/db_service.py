# services/db_wrapper.py
import sqlite3
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import uuid


# Helper
def now_iso() -> str:
    return datetime.utcnow().isoformat()


class Database:
    """
    Асинхронная обёртка для SQLite (aiosqlite) с поддержкой проектов (projects).
    - db_path: путь к .db файлу
    """

    def __init__(self, db_path: str = "db.sqlite"):
        self._conn = sqlite3.connect(db_path)
        self._create_tables()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def _create_tables(self):
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE,
                username TEXT
            );
            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                title TEXT,
                body TEXT,
                created_at TEXT,
                end_time TEXT,
                delivered BOOLEAN
            );
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                name TEXT NOT NULL,
                chat_history TEXT
            );
            """
        )

    # ---------------------
    # User methods
    # ---------------------
    def create_user(self, telegram_id: int, username: Optional[str] = None):
        self._conn.execute(
            "INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)",
            (telegram_id, username),
        )
        self._conn.commit()

    def create_notification(self, user_id: int, title: str, body: str,
                                  end_time: Optional[str] = None, delivered: bool = False):
        nid = str(uuid.uuid4())
        now = now_iso()

        self._conn.execute(
            "INSERT INTO notifications (id, user_id, title, body, created_at, end_time, delivered) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (nid, user_id, title, body, now, end_time, delivered)
        )

        self._conn.commit()

    def create_project(self, user_id: int, name: str, chat_history: str):
        nid = str(uuid.uuid4())
        self._conn.execute(
            "INSERT INTO projects (id, user_id, name, chat_history) VALUES (?, ?, ?, ?)",
            (nid, user_id, name, chat_history)
        )

        self._conn.commit()
    def delete_project(self, user_id, name: str):
        self._conn.execute(
            "DELETE FROM projects WHERE user_id = ? AND name = ?", (user_id, name)
        )

        self._conn.commit()

    def get_project_by_name(self, user_id, name: str):
        cur = self._conn.execute(
            "SELECT * FROM projects WHERE user_id = ? AND name = ?", (user_id, name)
        )

        return cur.fetchone()

    def list_notifications(self, user_id: int):
        cur = self._conn.execute(
            "SELECT * FROM notifications WHERE user_id = ?", (user_id,))
        return cur.fetchall()

    def list_projects(self, user_id: int):
        cur = self._conn.execute(
            "SELECT * FROM projects WHERE user_id = ?", (user_id,))
        return cur.fetchall()

    def update_notification_id(self, notification_id):
        self._conn.execute(
            "UPDATE notifications SET delivered = TRUE WHERE id = ?", (notification_id,)
        )

        self._conn.commit()

    def update_notification(self, name, time):
        print(name, time)
        self._conn.execute(
            "UPDATE notifications SET delivered = TRUE WHERE title = ? AND end_time = ?", (name, time)
        )

        self._conn.commit()