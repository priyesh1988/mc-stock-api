import os
import sqlite3
from datetime import date
from pathlib import Path

DEFAULT_DB_PATH = Path("signals.sqlite3")


def _db_path() -> Path:
    # For tests, you can override via env var
    p = os.getenv("SIGNALS_DB_PATH")
    return Path(p) if p else DEFAULT_DB_PATH


def init_db():
    path = _db_path()
    with sqlite3.connect(path) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_news_signal (
            symbol TEXT NOT NULL,
            day TEXT NOT NULL,
            sentiment REAL NOT NULL,
            article_count INTEGER NOT NULL,
            PRIMARY KEY (symbol, day)
        )
        """)
        conn.commit()


def get_signal(symbol: str, d: date):
    day = d.strftime("%Y-%m-%d")
    path = _db_path()
    with sqlite3.connect(path) as conn:
        cur = conn.execute(
            "SELECT sentiment, article_count FROM daily_news_signal WHERE symbol=? AND day=?",
            (symbol, day),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {"sentiment": float(row[0]), "article_count": int(row[1])}


def put_signal(symbol: str, d: date, sentiment: float, article_count: int):
    day = d.strftime("%Y-%m-%d")
    path = _db_path()
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO daily_news_signal(symbol, day, sentiment, article_count) VALUES(?,?,?,?)",
            (symbol, day, float(sentiment), int(article_count)),
        )
        conn.commit()
