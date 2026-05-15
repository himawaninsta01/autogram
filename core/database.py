import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "autogram.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS posts (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
            scheduled_at  DATETIME,
            posted_at     DATETIME,
            niche         TEXT,
            topic         TEXT,
            trend_score   REAL,
            caption       TEXT,
            hashtags      TEXT,
            image_path    TEXT,
            image_prompt  TEXT,
            qa_score      REAL,
            ig_post_id    TEXT,
            status        TEXT DEFAULT 'pending',
            retry_count   INTEGER DEFAULT 0,
            error_msg     TEXT
        );

        CREATE TABLE IF NOT EXISTS niche_config (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            niche     TEXT UNIQUE NOT NULL,
            enabled   BOOLEAN DEFAULT 1,
            priority  INTEGER DEFAULT 5,
            style     TEXT,
            added_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS pipeline_logs (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id    INTEGER REFERENCES posts(id),
            timestamp  DATETIME DEFAULT CURRENT_TIMESTAMP,
            stage      TEXT,
            status     TEXT,
            duration_s REAL,
            message    TEXT
        );

        CREATE TABLE IF NOT EXISTS trend_cache (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            niche       TEXT,
            topic       TEXT,
            score       REAL,
            source      TEXT,
            fetched_at  DATETIME,
            expires_at  DATETIME
        );
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully")

if __name__ == "__main__":
    init_db()