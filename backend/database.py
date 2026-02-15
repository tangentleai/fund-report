import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).resolve().parent / "data" / "funds.db"


def _get_fund_info_by_akshare(fund_code: str) -> Optional[Dict]:
    """使用 akshare 获取基金基本信息"""
    try:
        import akshare as ak

        try:
            info_df = ak.fund_individual_basic_info_xq(symbol=fund_code)
            if info_df is not None and not info_df.empty:
                info_map = {
                    str(row["item"]).strip(): str(row["value"]).strip()
                    for _, row in info_df.iterrows()
                }
                return {
                    "code": fund_code,
                    "name": info_map.get("基金名称", fund_code),
                    "full_name": info_map.get("基金全称"),
                    "manager": info_map.get("基金经理", "未知"),
                    "fund_type": info_map.get("基金类型"),
                    "fund_company": info_map.get("基金公司"),
                    "establish_date": info_map.get("成立时间"),
                    "latest_scale": info_map.get("最新规模"),
                    "custodian_bank": info_map.get("托管银行"),
                    "benchmark": info_map.get("业绩比较基准"),
                }
        except Exception:
            pass
        try:
            announcement_df = ak.fund_announcement_personnel_em(symbol=fund_code)
            if announcement_df is not None and not announcement_df.empty:
                name_col = None
                for col in announcement_df.columns:
                    if "名称" in str(col) or "name" in str(col).lower():
                        name_col = col
                        break
                if name_col:
                    fund_name = str(announcement_df.iloc[0][name_col])
                    fund_name = fund_name.split("-")[0].split("_")[0].strip()
                    return {
                        "code": fund_code,
                        "name": fund_name if fund_name else fund_code,
                        "full_name": None,
                        "manager": "未知",
                        "fund_type": None,
                        "fund_company": None,
                        "establish_date": None,
                        "latest_scale": None,
                        "custodian_bank": None,
                        "benchmark": None,
                    }
        except Exception:
            pass
    except Exception:
        pass
    return None


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
            full_name TEXT,
            manager TEXT,
            fund_type TEXT,
            fund_company TEXT,
            establish_date TEXT,
            latest_scale TEXT,
            custodian_bank TEXT,
            benchmark TEXT
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
    _migrate_funds_table(conn)
    conn.commit()
    _seed_funds(conn)
    conn.close()


def _migrate_funds_table(conn: sqlite3.Connection) -> None:
    cursor = conn.execute("PRAGMA table_info(funds)")
    columns = [row[1] for row in cursor.fetchall()]
    new_columns = {
        "full_name": "TEXT",
        "fund_company": "TEXT",
        "establish_date": "TEXT",
        "latest_scale": "TEXT",
        "custodian_bank": "TEXT",
        "benchmark": "TEXT",
    }
    for col_name, col_type in new_columns.items():
        if col_name not in columns:
            conn.execute(f"ALTER TABLE funds ADD COLUMN {col_name} {col_type}")


def _seed_funds(conn: sqlite3.Connection) -> None:
    count = conn.execute("SELECT COUNT(1) FROM funds").fetchone()[0]
    if count:
        return
    funds = [
        ("005827", "易方达蓝筹精选混合", None, "张坤", "混合型-偏股", None, None, None, None, None),
        ("003095", "中欧医疗健康混合A", None, "葛兰", "混合型-偏股", None, None, None, None, None),
        ("161725", "招商中证白酒指数", None, "侯昊", "指数型-股票", None, None, None, None, None),
    ]
    conn.executemany(
        "INSERT INTO funds (code, name, full_name, manager, fund_type, fund_company, establish_date, latest_scale, custodian_bank, benchmark) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        funds,
    )
    conn.commit()


def _save_fund_info(conn: sqlite3.Connection, fund_info: Dict) -> None:
    conn.execute(
        """INSERT OR REPLACE INTO funds 
           (code, name, full_name, manager, fund_type, fund_company, establish_date, latest_scale, custodian_bank, benchmark) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            fund_info["code"],
            fund_info["name"],
            fund_info.get("full_name"),
            fund_info["manager"],
            fund_info.get("fund_type"),
            fund_info.get("fund_company"),
            fund_info.get("establish_date"),
            fund_info.get("latest_scale"),
            fund_info.get("custodian_bank"),
            fund_info.get("benchmark"),
        ),
    )


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
        
        if not rows and query.isdigit() and len(query) == 6:
            fund_info = _get_fund_info_by_akshare(query)
            if fund_info:
                _save_fund_info(conn, fund_info)
                conn.commit()
                rows = conn.execute(
                    "SELECT * FROM funds WHERE code LIKE ? OR name LIKE ? ORDER BY code",
                    (like_query, like_query),
                ).fetchall()
    
    conn.close()
    return [dict(row) for row in rows]


def batch_import_funds(fund_codes: List[str]) -> Dict[str, Any]:
    """批量导入基金信息到数据库"""
    results = {"success": [], "failed": []}
    conn = _get_connection()
    
    for code in fund_codes:
        code = code.strip()
        if not code or not code.isdigit() or len(code) != 6:
            results["failed"].append({"code": code, "reason": "无效的基金代码格式"})
            continue
            
        existing = conn.execute("SELECT code FROM funds WHERE code = ?", (code,)).fetchone()
        if existing:
            results["success"].append({"code": code, "reason": "已存在"})
            continue
            
        fund_info = _get_fund_info_by_akshare(code)
        if fund_info:
            _save_fund_info(conn, fund_info)
            results["success"].append({"code": code, "name": fund_info["name"]})
        else:
            results["failed"].append({"code": code, "reason": "无法获取基金信息"})
    
    conn.commit()
    conn.close()
    return results


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
        SELECT f.code, f.name, f.full_name, f.manager, f.fund_type, f.fund_company, 
               f.establish_date, f.latest_scale, f.custodian_bank, f.benchmark, uf.created_at
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
        podcasts = conn.execute(
            """
            SELECT * FROM podcasts
            WHERE fund_code = ?
            ORDER BY report_period DESC
            """,
            (fund["code"],),
        ).fetchall()
        fund["podcasts"] = [_row_to_podcast(p) for p in podcasts] if podcasts else []
        items.append(fund)
    conn.close()
    return items


def list_all_funds() -> List[Dict[str, Any]]:
    """获取所有基金信息"""
    conn = _get_connection()
    rows = conn.execute(
        """
        SELECT code, name, full_name, manager, fund_type, fund_company, 
               establish_date, latest_scale, custodian_bank, benchmark
        FROM funds
        ORDER BY code
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_fund(fund_code: str) -> bool:
    """删除基金及其相关数据"""
    conn = _get_connection()
    existing = conn.execute("SELECT code FROM funds WHERE code = ?", (fund_code,)).fetchone()
    if not existing:
        conn.close()
        return False
    conn.execute("DELETE FROM podcasts WHERE fund_code = ?", (fund_code,))
    conn.execute("DELETE FROM user_funds WHERE fund_code = ?", (fund_code,))
    conn.execute("DELETE FROM funds WHERE code = ?", (fund_code,))
    conn.commit()
    conn.close()
    return True


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


def delete_podcast(podcast_id: int) -> Optional[Dict[str, Any]]:
    conn = _get_connection()
    row = conn.execute("SELECT * FROM podcasts WHERE id = ?", (podcast_id,)).fetchone()
    if not row:
        conn.close()
        return None
    podcast = _row_to_podcast(row)
    conn.execute("DELETE FROM podcasts WHERE id = ?", (podcast_id,))
    conn.commit()
    conn.close()
    return podcast


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
