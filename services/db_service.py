# services/db_service.py
import asyncpg
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from config import DATABASE_URL

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in environment (config.DATABASE_URL)")

def _now() -> datetime:
    return datetime.utcnow()

class PostgresDatabase:
    def __init__(self, dsn: str):
        self._dsn = dsn
        self._pool: Optional[asyncpg.Pool] = None

    async def init(self):
        self._pool = await asyncpg.create_pool(dsn=self._dsn, min_size=1, max_size=10)
        async with self._pool.acquire() as conn:
            # projects table + conversations referencing project_id
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    language_code TEXT,
                    created_at TIMESTAMP WITH TIME ZONE
                );
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id UUID PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP WITH TIME ZONE,
                    last_activity TIMESTAMP WITH TIME ZONE
                );
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id UUID PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
                    title TEXT,
                    created_at TIMESTAMP WITH TIME ZONE,
                    last_activity TIMESTAMP WITH TIME ZONE
                );
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id UUID PRIMARY KEY,
                    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
                    role TEXT,
                    content TEXT,
                    created_at TIMESTAMP WITH TIME ZONE,
                    token_count INTEGER DEFAULT 0,
                    meta JSONB
                );
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS usage (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    date DATE,
                    requests INTEGER DEFAULT 0,
                    tokens INTEGER DEFAULT 0,
                    UNIQUE(user_id, date)
                );
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    key TEXT,
                    value TEXT,
                    PRIMARY KEY(user_id, key)
                );
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS api_logs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER,
                    conversation_id UUID,
                    request_payload JSONB,
                    response_payload JSONB,
                    status TEXT,
                    created_at TIMESTAMP WITH TIME ZONE
                );
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id UUID PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    title TEXT,
                    body TEXT,
                    payload JSONB,
                    type TEXT,
                    created_at TIMESTAMP WITH TIME ZONE,
                    due_at TIMESTAMP WITH TIME ZONE,
                    read BOOLEAN DEFAULT FALSE,
                    delivered BOOLEAN DEFAULT FALSE
                );
            """)
            # индексы
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_conv_created ON messages(conversation_id, created_at);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_conv_user_last ON conversations(user_id, last_activity);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_projects_user_last ON projects(user_id, last_activity);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, read);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user_due ON notifications(user_id, due_at);")

    async def close(self):
        if self._pool:
            await self._pool.close()
            self._pool = None

    # ---------------- users ----------------
    async def create_user(self, telegram_id: int, username: Optional[str]=None,
                          first_name: Optional[str]=None, last_name: Optional[str]=None,
                          language_code: Optional[str]=None) -> int:
        assert self._pool is not None
        now = _now()
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO users (telegram_id, username, first_name, last_name, language_code, created_at)
                VALUES ($1,$2,$3,$4,$5,$6)
                ON CONFLICT (telegram_id) DO NOTHING
                RETURNING id
            """, telegram_id, username, first_name, last_name, language_code, now)
            if row and row['id']:
                return int(row['id'])
            row2 = await conn.fetchrow("SELECT id FROM users WHERE telegram_id = $1", telegram_id)
            return int(row2['id'])

    async def get_user_by_telegram(self, telegram_id: int) -> Optional[asyncpg.Record]:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            return await conn.fetchrow("SELECT * FROM users WHERE telegram_id = $1", telegram_id)

    async def get_user_by_id(self, user_id: int) -> Optional[asyncpg.Record]:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            return await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)


    async def ensure_user(self, tg_user: Dict[str, Any]) -> int:
        found = await self.get_user_by_telegram(tg_user["id"])
        if found:
            return int(found["id"])
        return await self.create_user(
            telegram_id=tg_user["id"],
            username=tg_user.get("username"),
            first_name=tg_user.get("first_name"),
            last_name=tg_user.get("last_name"),
            language_code=tg_user.get("language_code")
        )

    @staticmethod
    def _row_to_dict(row):
        """Преобразует asyncpg.Record -> dict, конвертирует UUID/datetime в строки."""
        if row is None:
            return None
        d = dict(row)
        # asyncpg returns UUID and datetime natively -> stringify them
        for k, v in list(d.items()):
            if isinstance(v, (uuid.UUID,)):
                d[k] = str(v)
            elif isinstance(v, (datetime,)):
                d[k] = v.isoformat()
        return d

    async def get_project_tree(self, project_id: str, conv_limit: int = 20, conv_message_limit: int = 20) -> Optional[Dict[str, Any]]:
        """
        Возвращает проект со списком бесед (ограничено conv_limit) и с сообщениями (ограничено conv_message_limit) для каждой беседы.
        """
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            proj_row = await conn.fetchrow("SELECT * FROM projects WHERE id = $1", uuid.UUID(project_id))
            if not proj_row:
                return None
            project = self._row_to_dict(proj_row)
            # conversations
            convs = await conn.fetch("SELECT * FROM conversations WHERE project_id = $1 ORDER BY last_activity DESC LIMIT $2", uuid.UUID(project_id), conv_limit)
            project['conversations'] = []
            for c in convs:
                cdict = self._row_to_dict(c)
                # messages (latest conv_message_limit)
                msgs = await conn.fetch("SELECT * FROM messages WHERE conversation_id = $1 ORDER BY created_at DESC LIMIT $2", uuid.UUID(cdict['id']), conv_message_limit)
                # return chronological order
                msgs = list(reversed([self._row_to_dict(m) for m in msgs]))
                cdict['messages'] = msgs
                project['conversations'].append(cdict)
            return project

    async def get_user_tree(self,
                            user_id: int,
                            project_limit: int = 50,
                            conv_limit: int = 20,
                            conv_message_limit: int = 20,
                            notif_limit: int = 50,
                            include_notifications: bool = True) -> Optional[Dict[str, Any]]:
        """
        Собирает вложенную структуру: user -> notifications -> projects -> conversations -> messages.
        Возвращает dict или None, если пользователь не найден.
        """
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            user_row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
            if not user_row:
                return None
            user = self._row_to_dict(user_row)

            # notifications (опционально)
            if include_notifications:
                notifs = await conn.fetch("SELECT * FROM notifications WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2", user_id, notif_limit)
                user['notifications'] = [self._row_to_dict(n) for n in notifs]
            else:
                user['notifications'] = []

            # projects
            projects = await conn.fetch("SELECT * FROM projects WHERE user_id = $1 ORDER BY last_activity DESC LIMIT $2", user_id, project_limit)
            user['projects'] = []
            for p in projects:
                p_dict = self._row_to_dict(p)
                # conversations in project
                convs = await conn.fetch("SELECT * FROM conversations WHERE project_id = $1 ORDER BY last_activity DESC LIMIT $2", uuid.UUID(p_dict['id']), conv_limit)
                p_dict['conversations'] = []
                for c in convs:
                    c_dict = self._row_to_dict(c)
                    msgs = await conn.fetch("SELECT * FROM messages WHERE conversation_id = $1 ORDER BY created_at DESC LIMIT $2", uuid.UUID(c_dict['id']), conv_message_limit)
                    c_dict['messages'] = list(reversed([self._row_to_dict(m) for m in msgs]))
                    p_dict['conversations'].append(c_dict)
                user['projects'].append(p_dict)

            return user

    # ---------------- projects ----------------
    async def create_project(self, user_id: int, name: str, description: Optional[str] = None) -> str:
        assert self._pool is not None
        project_id = uuid.uuid4()
        now = _now()
        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO projects (id, user_id, name, description, created_at, last_activity)
                VALUES ($1,$2,$3,$4,$5,$6)
            """, project_id, user_id, name, description, now, now)
        return str(project_id)

    async def list_projects(self, user_id: int, limit: int = 50) -> List[asyncpg.Record]:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM projects WHERE user_id = $1 ORDER BY last_activity DESC LIMIT $2", user_id, limit)
            return rows

    async def get_project(self, project_id: str) -> Optional[asyncpg.Record]:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            return await conn.fetchrow("SELECT * FROM projects WHERE id = $1", uuid.UUID(project_id))

    async def update_project(self, project_id: str, name: Optional[str] = None, description: Optional[str] = None):
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            if name is not None and description is not None:
                await conn.execute("UPDATE projects SET name = $1, description = $2, last_activity = $3 WHERE id = $4", name, description, _now(), uuid.UUID(project_id))
            elif name is not None:
                await conn.execute("UPDATE projects SET name = $1, last_activity = $2 WHERE id = $3", name, _now(), uuid.UUID(project_id))
            elif description is not None:
                await conn.execute("UPDATE projects SET description = $1, last_activity = $2 WHERE id = $3", description, _now(), uuid.UUID(project_id))

    async def delete_project(self, project_id: str):
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.execute("DELETE FROM projects WHERE id = $1", uuid.UUID(project_id))

    async def touch_project(self, project_id: str):
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.execute("UPDATE projects SET last_activity = $1 WHERE id = $2", _now(), uuid.UUID(project_id))

    # ---------------- conversations ----------------
    async def create_conversation(self, user_id: int, title: Optional[str] = "New chat", project_id: Optional[str] = None) -> str:
        assert self._pool is not None
        conv_id = uuid.uuid4()
        now = _now()
        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO conversations (id, user_id, project_id, title, created_at, last_activity)
                VALUES ($1,$2,$3,$4,$5,$6)
            """, conv_id, user_id, (uuid.UUID(project_id) if project_id else None), title, now, now)
        return str(conv_id)

    async def list_conversations(self, user_id: int, limit: int = 20, project_id: Optional[str] = None) -> List[asyncpg.Record]:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            if project_id:
                rows = await conn.fetch("SELECT * FROM conversations WHERE user_id = $1 AND project_id = $2 ORDER BY last_activity DESC LIMIT $3", user_id, uuid.UUID(project_id), limit)
            else:
                rows = await conn.fetch("SELECT * FROM conversations WHERE user_id = $1 ORDER BY last_activity DESC LIMIT $2", user_id, limit)
            return rows

    async def list_conversations_by_project(self, project_id: str, limit: int = 50) -> List[asyncpg.Record]:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM conversations WHERE project_id = $1 ORDER BY last_activity DESC LIMIT $2", uuid.UUID(project_id), limit)
            return rows

    async def get_conversation(self, conv_id: str) -> Optional[asyncpg.Record]:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            return await conn.fetchrow("SELECT * FROM conversations WHERE id = $1", uuid.UUID(conv_id))

    async def touch_conversation(self, conv_id: str):
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.execute("UPDATE conversations SET last_activity = $1 WHERE id = $2", _now(), uuid.UUID(conv_id))

    async def get_or_create_conversation(self, user_id: int, project_id: str | None):
        async with self._pool.acquire() as con:
            if project_id is None:
                # ищем беседу БЕЗ проекта
                existing = await con.fetchrow(
                    """
                    SELECT id FROM conversations
                    WHERE user_id = $1 AND project_id IS NULL
                    ORDER BY last_activity DESC
                    LIMIT 1
                    """,
                    user_id
                )
                if existing:
                    return str(existing["id"])

                created = await con.fetchrow(
                    """
                    INSERT INTO conversations (id, user_id, project_id, title, created_at, last_activity)
                    VALUES ($1, $2, NULL, $3, NOW(), NOW())
                    RETURNING id
                    """,
                    uuid.uuid4(), user_id, "Chat"
                )
                return str(created["id"])

            else:
                # ищем беседу ВНУТРИ проекта
                existing = await con.fetchrow(
                    """
                    SELECT id FROM conversations
                    WHERE user_id = $1 AND project_id = $2
                    ORDER BY last_activity DESC
                    LIMIT 1
                    """,
                    user_id, uuid.UUID(project_id)
                )
                if existing:
                    return str(existing["id"])

                created = await con.fetchrow(
                    """
                    INSERT INTO conversations (id, user_id, project_id, title, created_at, last_activity)
                    VALUES ($1, $2, $3, $4, NOW(), NOW())
                    RETURNING id
                    """,
                    uuid.uuid4(), user_id, uuid.UUID(project_id), "Project Chat"
                )
                return str(created["id"])


    # ---------------- messages ----------------
    async def save_message(self, conversation_id: str, role: str, content: str,
                           token_count: int = 0, meta: Optional[Dict[str, Any]] = None) -> str:
        assert self._pool is not None
        msg_id = uuid.uuid4()
        now = _now()
        meta_json = meta if meta is not None else {}
        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO messages (id, conversation_id, role, content, created_at, token_count, meta)
                VALUES ($1,$2,$3,$4,$5,$6,$7)
            """, msg_id, uuid.UUID(conversation_id), role, content, now, token_count, json.dumps(meta_json))
            await conn.execute("UPDATE conversations SET last_activity = $1 WHERE id = $2", now, uuid.UUID(conversation_id))
        return str(msg_id)

    async def get_recent_messages(self, conversation_id: str, limit: int = 20) -> List[asyncpg.Record]:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM messages WHERE conversation_id = $1 ORDER BY created_at DESC LIMIT $2", uuid.UUID(conversation_id), limit)
            return list(reversed(rows))

    async def get_context_by_token_budget(self, conversation_id: str, token_budget: int,
                                          token_counter_fn=None) -> List[Dict[str, Any]]:
        messages = await self.get_recent_messages(conversation_id, limit=1000)
        selected = []
        total = 0
        for m in reversed(messages):
            tokens = token_counter_fn(m['content']) if token_counter_fn else (m['token_count'] or 0)
            if total + tokens > token_budget and selected:
                break
            meta = m['meta']
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}
            selected.append({"role": m['role'], "content": m['content'], "meta": meta})
            total += tokens
        return selected

    async def add_message(self, conversation_id: str, role: str, content: str,
                          token_count: int = 0, meta: Optional[Dict[str, Any]] = None) -> str:
        assert self._pool is not None
        msg_id = uuid.uuid4()
        now = _now()
        meta_json = meta if meta is not None else {}

        async with self._pool.acquire() as con:
            await con.execute("""
                INSERT INTO messages (id, conversation_id, role, content, created_at, token_count, meta)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, msg_id, uuid.UUID(conversation_id), role, content, now,
                              token_count, json.dumps(meta_json))

            await con.execute("""
                UPDATE conversations SET last_activity = $1 WHERE id = $2
            """, now, uuid.UUID(conversation_id))

        return str(msg_id)

    async def get_messages(self, conversation_id: str, limit: int = 20):
        query = """
            SELECT role, content
            FROM messages
            WHERE conversation_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """

        async with self._pool.acquire() as con:
            rows = await con.fetch(query, conversation_id, limit)

        return [
            {"role": row["role"], "content": row["content"]}
            for row in reversed(rows)
        ]

    # ---------------- notifications ----------------
    async def create_notification(self, user_id: int, title: str, body: str,
                              payload: Optional[Dict[str, Any]] = None,
                              due_at: Optional[datetime] = None,
                              ntype: Optional[str] = None) -> str:
        assert self._pool is not None
        nid = uuid.uuid4()
        now = _now()
        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO notifications (id, user_id, title, body, payload, type, created_at, due_at, read, delivered)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,false,false)
            """, nid, user_id, title, body, json.dumps(payload or {}), ntype, now, due_at)
        return str(nid)

    async def list_notifications(self, user_id: int, unread_only: bool = False, limit: int = 50) -> List[asyncpg.Record]:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            if unread_only:
                return await conn.fetch("SELECT * FROM notifications WHERE user_id = $1 AND read = false ORDER BY created_at DESC LIMIT $2", user_id, limit)
            return await conn.fetch("SELECT * FROM notifications WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2", user_id, limit)

    async def get_notification(self, notification_id: str) -> Optional[asyncpg.Record]:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            return await conn.fetchrow("SELECT * FROM notifications WHERE id = $1", uuid.UUID(notification_id))

    async def mark_notification_read(self, notification_id: str):
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.execute("UPDATE notifications SET read = true WHERE id = $1", uuid.UUID(notification_id))

    async def mark_all_read(self, user_id: int):
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.execute("UPDATE notifications SET read = true WHERE user_id = $1", user_id)

    async def get_unread_count(self, user_id: int) -> int:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT count(*) AS cnt FROM notifications WHERE user_id = $1 AND read = false", user_id)
            return int(row['cnt'])

    # util for scheduler: fetch due notifications up to `until`
    async def fetch_due_notifications(self, until: datetime, limit: int = 100) -> List[asyncpg.Record]:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            return await conn.fetch("SELECT * FROM notifications WHERE due_at IS NOT NULL AND delivered = false AND due_at <= $1 ORDER BY due_at ASC LIMIT $2", until, limit)

    async def mark_delivered(self, notification_id: str):
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.execute("UPDATE notifications SET delivered = true WHERE id = $1", uuid.UUID(notification_id))

    # ---------------- usage & logs ----------------
    async def increment_usage(self, user_id: int, tokens: int = 0, reqs: int = 1):
        assert self._pool is not None
        date = _now().date()
        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO usage (user_id, date, requests, tokens)
                VALUES ($1,$2,$3,$4)
                ON CONFLICT (user_id, date) DO UPDATE
                  SET requests = usage.requests + EXCLUDED.requests,
                      tokens = usage.tokens + EXCLUDED.tokens
            """, user_id, date, reqs, tokens)

    async def get_usage(self, user_id: int, since_days: int = 7) -> List[asyncpg.Record]:
        assert self._pool is not None
        cutoff = _now().date() - timedelta(days=since_days)
        async with self._pool.acquire() as conn:
            return await conn.fetch("SELECT * FROM usage WHERE user_id = $1 AND date >= $2 ORDER BY date DESC", user_id, cutoff)

    async def log_api(self, user_id: Optional[int], conversation_id: Optional[str],
                      request_payload: Dict[str, Any], response_payload: Dict[str, Any], status: str = "ok"):
        assert self._pool is not None
        now = _now()
        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO api_logs (user_id, conversation_id, request_payload, response_payload, status, created_at)
                VALUES ($1,$2,$3,$4,$5,$6)
            """, user_id, (uuid.UUID(conversation_id) if conversation_id else None),
                 json.dumps(request_payload, ensure_ascii=False), json.dumps(response_payload, ensure_ascii=False),
                 status, now)

    # ---------------- settings ----------------
    async def set_setting(self, user_id: int, key: str, value: str):
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO settings (user_id, key, value) VALUES ($1,$2,$3)
                ON CONFLICT (user_id, key) DO UPDATE SET value = EXCLUDED.value
            """, user_id, key, value)

    async def get_setting(self, user_id: int, key: str) -> Optional[str]:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT value FROM settings WHERE user_id = $1 AND key = $2", user_id, key)
            return row['value'] if row else None

    # ---------------- utilities ----------------
    async def search_messages(self, query: str, limit: int = 20) -> List[asyncpg.Record]:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            return await conn.fetch("SELECT * FROM messages WHERE content ILIKE $1 ORDER BY created_at DESC LIMIT $2", f"%{query}%", limit)

    async def clear_conversation(self, conversation_id: str):
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.execute("DELETE FROM messages WHERE conversation_id = $1", uuid.UUID(conversation_id))
            await conn.execute("DELETE FROM conversations WHERE id = $1", uuid.UUID(conversation_id))

# singleton
db = PostgresDatabase(DATABASE_URL)
