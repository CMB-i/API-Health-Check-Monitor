import sqlite3
from pathlib import Path
from datetime import datetime

# Database file path
DB_PATH = Path(__file__).parent / "health.db"


def init_db():
    """Create database and table if not exists"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS health_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        url TEXT,
        status_code INTEGER,
        latency_ms REAL,
        is_up INTEGER,
        error TEXT,
        timestamp TEXT
    )
    """)

    conn.commit()
    conn.close()


def log_results(results):
    """
    Insert multiple API results into DB
    :param results: list of dictionaries from engine
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for result in results:
        cursor.execute("""
        INSERT INTO health_logs (
            name, url, status_code, latency_ms, is_up, error, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            result.get("name"),
            result.get("url"),
            result.get("status_code"),
            result.get("latency_ms"),
            int(result.get("is_up", False)),
            result.get("error"),
            datetime.now().isoformat()
        ))

    conn.commit()
    conn.close()


def safe_log_results(results):
    """Wrapper to prevent crashes during logging"""
    try:
        log_results(results)
    except Exception as e:
        print(f"[LOGGER ERROR] {e}")


def get_recent_logs(limit=5):
    """Fetch most recent API logs"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, status_code, latency_ms, timestamp
        FROM health_logs
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    return rows


def get_avg_latency():
    """Calculate average latency of all logs"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT AVG(latency_ms) FROM health_logs
    """)

    avg = cursor.fetchone()[0]
    conn.close()

    return avg