import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "autogram.db"

def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Buat tabel partners jika belum ada
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS partners (
            id                TEXT PRIMARY KEY,
            name              TEXT NOT NULL,
            website_url       TEXT,
            niche_list        TEXT, -- JSON Array string
            theme_accent      TEXT, -- RGB Accent 1 (e.g. "42,67,45")
            theme_accent2     TEXT, -- RGB Accent 2
            theme_bg          TEXT, -- RGB Background
            supabase_url      TEXT,
            supabase_key      TEXT,
            ig_username       TEXT,
            ig_password       TEXT,
            telegram_token    TEXT,
            telegram_chat_id  TEXT,
            created_at        DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. Buat tabel-tabel utama jika belum ada (skema dasar)
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
            error_msg     TEXT,
            post_format   TEXT DEFAULT 'single',
            series_id     TEXT,
            series_index  INTEGER
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

        CREATE TABLE IF NOT EXISTS seo_rank_history (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            partner_id   TEXT REFERENCES partners(id),
            keyword      TEXT NOT NULL,
            rank         INTEGER,
            checked_at   DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 3. Fungsi pembantu migrasi kolom partner_id & format kampanye
    def add_column_if_not_exists(table, column, definition):
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        if column not in columns:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            print(f"[MIGRATION] Kolom '{column}' berhasil ditambahkan ke tabel '{table}'")

    # Jalankan migrasi kolom partner_id
    add_column_if_not_exists("posts", "partner_id", "TEXT REFERENCES partners(id) DEFAULT 'duagaris'")
    add_column_if_not_exists("niche_config", "partner_id", "TEXT REFERENCES partners(id) DEFAULT 'duagaris'")
    add_column_if_not_exists("pipeline_logs", "partner_id", "TEXT REFERENCES partners(id) DEFAULT 'duagaris'")
    add_column_if_not_exists("trend_cache", "partner_id", "TEXT REFERENCES partners(id) DEFAULT 'duagaris'")
    
    # Migrasi format post & campaign 
    add_column_if_not_exists("posts", "post_format", "TEXT DEFAULT 'single'")
    add_column_if_not_exists("posts", "series_id", "TEXT")
    add_column_if_not_exists("posts", "series_index", "INTEGER")

    # 4. Masukkan mitra default (Dua Garis Landscape) jika tabel kosong
    cursor.execute("SELECT COUNT(*) FROM partners")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO partners (id, name, website_url, niche_list, theme_accent, theme_accent2, theme_bg)
            VALUES (
                'duagaris', 
                'Dua Garis Landscape', 
                'https://duagarislandscape.vercel.app/',
                '["jasa taman", "tanaman hias", "desain taman", "tips berkebun", "rumput taman"]',
                '42,67,45', 
                '74,122,77', 
                '8,20,12'
            )
        """)
        print("[DB] Mitra default 'Dua Garis Landscape' berhasil dimasukkan")

    # Masukkan mitra uji coba kedua (Superchronos AI)
    cursor.execute("SELECT COUNT(*) FROM partners WHERE id = 'superchronos'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO partners (id, name, website_url, niche_list, theme_accent, theme_accent2, theme_bg)
            VALUES (
                'superchronos', 
                'Superchronos AI', 
                'https://superchronos.ai/',
                '["AI", "teknologi", "desain", "bisnis online", "tips produktivitas"]',
                '0,229,160', 
                '0,180,255', 
                '8,8,24'
            )
        """)
        print("[DB] Mitra uji coba 'Superchronos AI' berhasil dimasukkan")

    conn.commit()
    conn.close()
    print("[DB] Database initialized successfully")

if __name__ == "__main__":
    init_db()