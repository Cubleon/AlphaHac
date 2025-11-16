# config.py
import os
from urllib.parse import quote_plus

def _make_db_url():
    env = os.getenv
    db_url = env("DATABASE_URL")
    if db_url:
        return db_url
    user = env("POSTGRES_USER", "postgres")
    pwd = env("POSTGRES_PASSWORD", "")
    host = env("DB_HOST", env("POSTGRES_HOST", "localhost"))
    port = env("DB_PORT", env("POSTGRES_PORT", "5432"))
    db = env("POSTGRES_DB", "alphabot")
    pwd_enc = quote_plus(pwd)
    return f"postgresql://{user}:{pwd_enc}@{host}:{port}/{db}"

DATABASE_URL = _make_db_url()
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
