import aiosqlite
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
    def __init__(self, db_path: str = "bot.db"):
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()

    async def init(self):
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL;")
        await self._conn.execute("PRAGMA foreign_keys=ON;")
        await self._create_tables()
        await self._conn.commit()

    async def close(self):
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def _create_tables(self):
        assert self._conn is not None
        async with self._lock:
            await self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    telegram_id INTEGER UNIQUE,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    language_code TEXT,
                    created_at TEXT
                );

                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT,
                    last_activity TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER,
                    project_id TEXT,
                    title TEXT,
                    created_at TEXT,
                    last_activity TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    role TEXT,
                    content TEXT,
                    created_at TEXT,
                    token_count INTEGER DEFAULT 0,
                    meta TEXT,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    date TEXT,
                    requests INTEGER DEFAULT 0,
                    tokens INTEGER DEFAULT 0,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE(user_id, date)
                );

                CREATE TABLE IF NOT EXISTS settings (
                    user_id INTEGER,
                    key TEXT,
                    value TEXT,
                    PRIMARY KEY(user_id, key),
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS api_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    conversation_id TEXT,
                    request_payload TEXT,
                    response_payload TEXT,
                    status TEXT,
                    created_at TEXT
                );

                -- FTS5 for messages content search (optional)
                CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
                    content,
                    message_id UNINDEXED
                );
                """
            )
            await self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_conv_created ON messages(conversation_id, created_at);"
            )
            await self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_conv_user_last ON conversations(user_id, last_activity);"
            )
            await self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_projects_user_last ON projects(user_id, last_activity);"
            )
            await self._conn.commit()

    # ---------------------
    # User methods
    # ---------------------
    async def create_user(self, telegram_id: int, username: Optional[str] = None,
                          first_name: Optional[str] = None, last_name: Optional[str] = None,
                          language_code: Optional[str] = None) -> int:
        assert self._conn is not None
        now = now_iso()
        async with self._lock:
            await self._conn.execute(
                "INSERT OR IGNORE INTO users (telegram_id, username, first_name, last_name, language_code, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (telegram_id, username, first_name, last_name, language_code, now),
            )
            await self._conn.commit()
            cur = await self._conn.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
            row = await cur.fetchone()
            return int(row["id"])

    async def get_user_by_telegram(self, telegram_id: int) -> Optional[aiosqlite.Row]:
        assert self._conn is not None
        cur = await self._conn.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        return await cur.fetchone()

    async def ensure_user(self, tg_user: Dict[str, Any]) -> int:
        found = await self.get_user_by_telegram(tg_user["id"])
        if found:
            return int(found["id"])
        return await self.create_user(
            telegram_id=tg_user["id"],
            username=tg_user.get("username"),
            first_name=tg_user.get("first_name"),
            last_name=tg_user.get("last_name"),
            language_code=tg_user.get("language_code"),
        )

    # ---------------------
    # Projects
    # ---------------------
    async def create_project(self, user_id: int, name: str, description: Optional[str] = None) -> str:
        assert self._conn is not None
        project_id = str(uuid.uuid4())
        now = now_iso()
        async with self._lock:
            await self._conn.execute(
                "INSERT INTO projects (id, user_id, name, description, created_at, last_activity) VALUES (?, ?, ?, ?, ?, ?)",
                (project_id, user_id, name, description, now, now),
            )
            await self._conn.commit()
        return project_id

    async def list_projects(self, user_id: int, limit: int = 50) -> List[aiosqlite.Row]:
        assert self._conn is not None
        cur = await self._conn.execute("SELECT * FROM projects WHERE user_id = ? ORDER BY last_activity DESC LIMIT ?", (user_id, limit))
        rows = await cur.fetchall()
        return rows

    async def get_project(self, project_id: str) -> Optional[aiosqlite.Row]:
        assert self._conn is not None
        cur = await self._conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        return await cur.fetchone()

    async def update_project(self, project_id: str, name: Optional[str] = None, description: Optional[str] = None):
        assert self._conn is not None
        now = now_iso()
        async with self._lock:
            if name is not None and description is not None:
                await self._conn.execute("UPDATE projects SET name = ?, description = ?, last_activity = ? WHERE id = ?", (name, description, now, project_id))
            elif name is not None:
                await self._conn.execute("UPDATE projects SET name = ?, last_activity = ? WHERE id = ?", (name, now, project_id))
            elif description is not None:
                await self._conn.execute("UPDATE projects SET description = ?, last_activity = ? WHERE id = ?", (description, now, project_id))
            await self._conn.commit()

    async def delete_project(self, project_id: str):
        assert self._conn is not None
        async with self._lock:
            await self._conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            await self._conn.commit()

    async def touch_project(self, project_id: str):
        assert self._conn is not None
        now = now_iso()
        async with self._lock:
            await self._conn.execute("UPDATE projects SET last_activity = ? WHERE id = ?", (now, project_id))
            await self._conn.commit()

    # ---------------------
    # Conversation methods
    # ---------------------
    async def create_conversation(self, user_id: int, title: Optional[str] = "New chat", project_id: Optional[str] = None) -> str:
        assert self._conn is not None
        conv_id = str(uuid.uuid4())
        now = now_iso()
        async with self._lock:
            await self._conn.execute(
                "INSERT INTO conversations (id, user_id, project_id, title, created_at, last_activity) VALUES (?, ?, ?, ?, ?, ?)",
                (conv_id, user_id, project_id, title, now, now),
            )
            await self._conn.commit()
        return conv_id

    async def list_conversations(self, user_id: int, limit: int = 20, project_id: Optional[str] = None) -> List[aiosqlite.Row]:
        assert self._conn is not None
        if project_id:
            cur = await self._conn.execute("SELECT * FROM conversations WHERE user_id = ? AND project_id = ? ORDER BY last_activity DESC LIMIT ?", (user_id, project_id, limit))
        else:
            cur = await self._conn.execute("SELECT * FROM conversations WHERE user_id = ? ORDER BY last_activity DESC LIMIT ?", (user_id, limit))
        rows = await cur.fetchall()
        return rows

    async def list_conversations_by_project(self, project_id: str, limit: int = 50) -> List[aiosqlite.Row]:
        assert self._conn is not None
        cur = await self._conn.execute("SELECT * FROM conversations WHERE project_id = ? ORDER BY last_activity DESC LIMIT ?", (project_id, limit))
        rows = await cur.fetchall()
        return rows

    async def get_conversation(self, conv_id: str) -> Optional[aiosqlite.Row]:
        assert self._conn is not None
        cur = await self._conn.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,))
        return await cur.fetchone()

    async def touch_conversation(self, conv_id: str):
        assert self._conn is not None
        now = now_iso()
        async with self._lock:
            await self._conn.execute("UPDATE conversations SET last_activity = ? WHERE id = ?", (now, conv_id))
            await self._conn.commit()

    # ---------------------
    # Messages
    # ---------------------
    async def save_message(self, conversation_id: str, role: str, content: str,
                           token_count: int = 0, meta: Optional[Dict[str, Any]] = None) -> str:
        assert self._conn is not None
        msg_id = str(uuid.uuid4())
        now = now_iso()
        meta_json = json.dumps(meta or {})
        async with self._lock:
            await self._conn.execute(
                "INSERT INTO messages (id, conversation_id, role, content, created_at, token_count, meta) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (msg_id, conversation_id, role, content, now, token_count, meta_json),
            )
            try:
                await self._conn.execute(
                    "INSERT INTO messages_fts(rowid, content, message_id) VALUES ((SELECT rowid FROM messages WHERE id = ?), ?, ?)",
                    (msg_id, content, msg_id),
                )
            except Exception:
                pass
            await self._conn.execute("UPDATE conversations SET last_activity = ? WHERE id = ?", (now, conversation_id))
            await self._conn.commit()
        return msg_id

    async def get_recent_messages(self, conversation_id: str, limit: int = 20) -> List[aiosqlite.Row]:
        assert self._conn is not None
        cur = await self._conn.execute("SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at DESC LIMIT ?", (conversation_id, limit))
        rows = await cur.fetchall()
        return list(reversed(rows))  # return in chronological order

    async def get_context_by_token_budget(self, conversation_id: str, token_budget: int,
                                          token_counter_fn=None) -> List[Dict[str, Any]]:
        messages = await self.get_recent_messages(conversation_id, limit=1000)
        selected = []
        total = 0
        for m in reversed(messages):  # oldest -> newest
            tokens = token_counter_fn(m["content"]) if token_counter_fn else (m["token_count"] or 0)
            if total + tokens > token_budget and selected:
                break
            selected.append({"role": m["role"], "content": m["content"], "meta": json.loads(m["meta"] or "{}")})
            total += tokens
        return selected

    # ---------------------
    # Usage & logs
    # ---------------------
    async def increment_usage(self, user_id: int, tokens: int = 0, reqs: int = 1):
        assert self._conn is not None
        date = datetime.utcnow().date().isoformat()
        async with self._lock:
            await self._conn.execute(
                """
                INSERT INTO usage (user_id, date, requests, tokens)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, date) DO UPDATE SET
                    requests = requests + excluded.requests,
                    tokens = tokens + excluded.tokens
                """,
                (user_id, date, reqs, tokens),
            )
            await self._conn.commit()

    async def get_usage(self, user_id: int, since_days: int = 7) -> List[aiosqlite.Row]:
        assert self._conn is not None
        cutoff = (datetime.utcnow().date() - timedelta(days=since_days)).isoformat()
        cur = await self._conn.execute("SELECT * FROM usage WHERE user_id = ? AND date >= ? ORDER BY date DESC", (user_id, cutoff))
        rows = await cur.fetchall()
        return rows

    async def log_api(self, user_id: Optional[int], conversation_id: Optional[str],
                      request_payload: Dict[str, Any], response_payload: Dict[str, Any], status: str = "ok"):
        assert self._conn is not None
        now = now_iso()
        async with self._lock:
            await self._conn.execute(
                "INSERT INTO api_logs (user_id, conversation_id, request_payload, response_payload, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, conversation_id, json.dumps(request_payload, ensure_ascii=False), json.dumps(response_payload, ensure_ascii=False), status, now),
            )
            await self._conn.commit()

    # ---------------------
    # Settings
    # ---------------------
    async def set_setting(self, user_id: int, key: str, value: str):
        assert self._conn is not None
        async with self._lock:
            await self._conn.execute(
                "INSERT INTO settings (user_id, key, value) VALUES (?, ?, ?) ON CONFLICT(user_id, key) DO UPDATE SET value = excluded.value",
                (user_id, key, value),
            )
            await self._conn.commit()

    async def get_setting(self, user_id: int, key: str) -> Optional[str]:
        assert self._conn is not None
        cur = await self._conn.execute_fetchone("SELECT value FROM settings WHERE user_id = ? AND key = ?", (user_id, key))
        if cur:
            return cur["value"]
        return None

    # ---------------------
    # Utilities
    # ---------------------
    async def search_messages(self, query: str, limit: int = 20) -> List[aiosqlite.Row]:
        assert self._conn is not None
        try:
            cur = await self._conn.execute(
                "SELECT m.* FROM messages_fts f JOIN messages m ON f.message_id = m.id WHERE messages_fts MATCH ? LIMIT ?",
                (query, limit),
            )
            rows = await cur.fetchall()
            return rows
        except Exception:
            cur = await self._conn.execute(
                "SELECT * FROM messages WHERE content LIKE ? ORDER BY created_at DESC LIMIT ?",
                (f"%{query}%", limit),
            )
            rows = await cur.fetchall()
            return rows

    async def clear_conversation(self, conversation_id: str):
        assert self._conn is not None
        async with self._lock:
            await self._conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
            await self._conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            try:
                await self._conn.execute("DELETE FROM messages_fts WHERE message_id = ?", (conversation_id,))
            except Exception:
                pass
            await self._conn.commit()
