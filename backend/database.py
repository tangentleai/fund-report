import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).resolve().parent / "data" / "funds.db"


def _get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _get_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS funds (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            manager TEXT,
            fund_type TEXT
        );
        CREATE TABLE IF NOT EXISTS user_funds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            fund_code TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(device_id, fund_code)
        );
        CREATE TABLE IF NOT EXISTS podcasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fund_code TEXT NOT NULL,
            report_period TEXT NOT NULL,
            title TEXT,
            audio_url TEXT,
            duration INTEGER,
            transcript TEXT,
            status TEXT DEFAULT 'pending',
            error_msg TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(fund_code, report_period)
        );
        CREATE INDEX IF NOT EXISTS idx_user_funds_device ON user_funds(device_id);
        CREATE INDEX IF NOT EXISTS idx_podcasts_status ON podcasts(status);
        """
    )
    conn.commit()
    _seed_funds(conn)
    conn.close()


def _seed_funds(conn: sqlite3.Connection) -> None:
    count = conn.execute("SELECT COUNT(1) FROM funds").fetchone()[0]
    if count:
        return
    funds = [
        ("005827", "易方达蓝筹精选混合", "张坤", "混合型-偏股"),
        ("003095", "中欧医疗健康混合A", "葛兰", "混合型-偏股"),
        ("161725", "招商中证白酒指数", "侯昊", "指数型-股票"),
    ]
    conn.executemany(
        "INSERT INTO funds (code, name, manager, fund_type) VALUES (?, ?, ?, ?)",
        funds,
    )
    conn.commit()


def search_funds(query: str) -> List[Dict[str, Any]]:
    conn = _get_connection()
    if not query:
        rows = conn.execute("SELECT * FROM funds ORDER BY code").fetchall()
    else:
        like_query = f"%{query}%"
        rows = conn.execute(
            "SELECT * FROM funds WHERE code LIKE ? OR name LIKE ? ORDER BY code",
            (like_query, like_query),
        ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_fund_by_code(fund_code: str) -> Optional[Dict[str, Any]]:
    conn = _get_connection()
    row = conn.execute("SELECT * FROM funds WHERE code = ?", (fund_code,)).fetchone()
    conn.close()
    return dict(row) if row else None


def add_user_fund(device_id: str, fund_code: str) -> None:
    conn = _get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO user_funds (device_id, fund_code) VALUES (?, ?)",
        (device_id, fund_code),
    )
    conn.commit()
    conn.close()


def delete_user_fund(device_id: str, fund_code: str) -> None:
    conn = _get_connection()
    conn.execute(
        "DELETE FROM user_funds WHERE device_id = ? AND fund_code = ?",
        (device_id, fund_code),
    )
    conn.commit()
    conn.close()


def list_user_funds(device_id: str) -> List[Dict[str, Any]]:
    conn = _get_connection()
    rows = conn.execute(
        """
        SELECT f.code, f.name, f.manager, f.fund_type, uf.created_at
        FROM user_funds uf
        JOIN funds f ON uf.fund_code = f.code
        WHERE uf.device_id = ?
        ORDER BY uf.created_at DESC
        """,
        (device_id,),
    ).fetchall()
    items = []
    for row in rows:
        fund = dict(row)
        podcast = conn.execute(
            """
            SELECT * FROM podcasts
            WHERE fund_code = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (fund["code"],),
        ).fetchone()
        fund["podcast"] = _row_to_podcast(podcast) if podcast else None
        items.append(fund)
    conn.close()
    return items


def get_latest_podcast(fund_code: str, report_period: str) -> Optional[Dict[str, Any]]:
    conn = _get_connection()
    row = conn.execute(
        """
        SELECT * FROM podcasts
        WHERE fund_code = ? AND report_period = ?
        LIMIT 1
        """,
        (fund_code, report_period),
    ).fetchone()
    conn.close()
    return _row_to_podcast(row) if row else None


def create_podcast_task(fund_code: str, report_period: str, title: str) -> int:
    conn = _get_connection()
    row = conn.execute(
        """
        INSERT INTO podcasts (fund_code, report_period, title, status)
        VALUES (?, ?, ?, 'pending')
        """,
        (fund_code, report_period, title),
    )
    conn.commit()
    task_id = row.lastrowid
    conn.close()
    return task_id


def update_podcast(podcast_id: int, updates: Dict[str, Any]) -> None:
    conn = _get_connection()
    data = updates.copy()
    if "transcript" in data and isinstance(data["transcript"], list):
        data["transcript"] = json.dumps(data["transcript"], ensure_ascii=False)
    columns = ", ".join([f"{key} = ?" for key in data.keys()])
    values = list(data.values())
    values.append(podcast_id)
    conn.execute(f"UPDATE podcasts SET {columns} WHERE id = ?", values)
    conn.commit()
    conn.close()


def get_podcast(podcast_id: int) -> Optional[Dict[str, Any]]:
    conn = _get_connection()
    row = conn.execute("SELECT * FROM podcasts WHERE id = ?", (podcast_id,)).fetchone()
    conn.close()
    return _row_to_podcast(row) if row else None


def get_podcast_status(podcast_id: int) -> Optional[Dict[str, Any]]:
    conn = _get_connection()
    row = conn.execute(
        "SELECT id, fund_code, report_period, status, audio_url, duration, error_msg FROM podcasts WHERE id = ?",
        (podcast_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def _row_to_podcast(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    data = dict(row)
    if data.get("transcript"):
        try:
            data["transcript"] = json.loads(data["transcript"])
        except json.JSONDecodeError:
            data["transcript"] = []
    return data
