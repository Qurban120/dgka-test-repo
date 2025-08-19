import os
import json
import sqlite3
from contextlib import contextmanager
from typing import Dict, Any, Optional, List

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'rhi.db')
JSON_SEED = os.path.join(BASE_DIR, 'rhi-data.json')

RHI_VALUE_FIELD_MAP: Dict[str, str] = {
    'rhi96': 'value',
    'rhi97': 'value',
    'rhi98': 'value',
    'rhi102': 'value',
    'rhi103': 'value',
    'rhi104': 'value',
}


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(drop: bool = False) -> None:
    with get_conn() as conn:
        cur = conn.cursor()
        if drop:
            cur.execute('DROP TABLE IF EXISTS rhi_points')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS rhi_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rhi_id TEXT NOT NULL,
                period TEXT NOT NULL,
                value REAL NOT NULL,
                UNIQUE(rhi_id, period)
            )
        ''')


def _insert_point(conn: sqlite3.Connection, rhi_id: str, period: str, value: float) -> None:
    conn.execute(
        'INSERT INTO rhi_points (rhi_id, period, value) VALUES (?, ?, ?)\n\t\tON CONFLICT(rhi_id, period) DO UPDATE SET value=excluded.value',
        (rhi_id, period, value),
    )


def seed_from_json(file_path: Optional[str] = None, clear_existing: bool = True) -> None:
    path = file_path or JSON_SEED
    if not os.path.exists(path):
        return
    with open(path, 'r', encoding='utf-8') as f:
        payload = json.load(f)
    with get_conn() as conn:
        if clear_existing:
            conn.execute('DELETE FROM rhi_points')
        for rhi_id, content in payload.items():
            for item in content.get('data', []):
                _insert_point(conn, rhi_id, item['period'], float(item.get('value') or 0.0))


def upsert_data_point(rhi_id: str, period: str, value: float) -> None:
    with get_conn() as conn:
        _insert_point(conn, rhi_id, period, value)


def update_data_point(rhi_id: str, period: str, value: Optional[float] = None) -> int:
    with get_conn() as conn:
        row = conn.execute('SELECT id FROM rhi_points WHERE rhi_id=? AND period=?', (rhi_id, period)).fetchone()
        if not row:
            return 0
        if value is None:
            return 0
        conn.execute('UPDATE rhi_points SET value=? WHERE id=?', (value, row['id']))
        return 1


def delete_data_point(rhi_id: str, period: str) -> int:
    with get_conn() as conn:
        res = conn.execute('DELETE FROM rhi_points WHERE rhi_id=? AND period=?', (rhi_id, period))
        return res.rowcount


def _order_clause() -> str:
    # Periods are MM-YYYY
    return 'CAST(SUBSTR(period, 4, 4) AS INTEGER), CAST(SUBSTR(period, 1, 2) AS INTEGER)'


def _collect_rhi(conn: sqlite3.Connection, rhi_id: str) -> Dict[str, Any]:
    rows = conn.execute(f'SELECT period, value FROM rhi_points WHERE rhi_id=? ORDER BY {_order_clause()}', (rhi_id,)).fetchall()
    return {'data': [{'period': r['period'], 'value': r['value']} for r in rows]}


def fetch_all_data() -> Dict[str, Any]:
    with get_conn() as conn:
        result: Dict[str, Any] = {}
        rhi_ids = set(RHI_VALUE_FIELD_MAP.keys())
        for (rid,) in conn.execute('SELECT DISTINCT rhi_id FROM rhi_points'):
            rhi_ids.add(rid)
        for rhi_id in sorted(rhi_ids):
            result[rhi_id] = _collect_rhi(conn, rhi_id)
        return result


def get_rhi(rhi_id: str) -> Dict[str, Any]:
    with get_conn() as conn:
        return _collect_rhi(conn, rhi_id)

