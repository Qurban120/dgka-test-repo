import os
import json
import sqlite3
from contextlib import contextmanager
from typing import Dict, Any, Optional, List

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'rhi.db')
JSON_SEED = os.path.join(BASE_DIR, 'rhi-data.json')

# RHI IDs and their fields
VALUE_FIELD_MAP: Dict[str, str] = {
    'rhi96': 'value',
    'rhi97': 'value',
    'rhi98': 'value',
    'rhi102': 'hours',
    'rhi103': 'hours',
    'rhi104': 'hours',
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
                conn.execute(
                    'INSERT INTO rhi_points (rhi_id, period, value) VALUES (?, ?, ?)\n\t\tON CONFLICT(rhi_id, period) DO UPDATE SET value=excluded.value',
                    (rhi_id, item['period'], float(item.get('value') or item.get('hours') or 0.0)),
                )


def upsert_data_point(rhi_id: str, period: str, value: float) -> None:
    with get_conn() as conn:
        conn.execute(
            'INSERT INTO rhi_points (rhi_id, period, value) VALUES (?, ?, ?)\n\t\tON CONFLICT(rhi_id, period) DO UPDATE SET value=excluded.value',
            (rhi_id, period, value),
        )


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


def _order_clause_for_rhi(rhi_id: str) -> str:
    # RHI uses monthly MM-YYYY periods
    return 'CAST(SUBSTR(period, 4, 4) AS INTEGER), CAST(SUBSTR(period, 1, 2) AS INTEGER)'


def _collect_rhi(conn: sqlite3.Connection, rhi_id: str) -> Dict[str, Any]:
    field = VALUE_FIELD_MAP[rhi_id]
    order_clause = _order_clause_for_rhi(rhi_id)
    rows = conn.execute(f'SELECT period, value FROM rhi_points WHERE rhi_id=? ORDER BY {order_clause}', (rhi_id,)).fetchall()
    return {'data': [{'period': r['period'], field: r['value']} for r in rows]}


def fetch_all_data() -> Dict[str, Any]:
    with get_conn() as conn:
        result: Dict[str, Any] = {}
        # include any ids present + empty defaults
        ids = set(VALUE_FIELD_MAP.keys())
        for (rid,) in conn.execute('SELECT DISTINCT rhi_id FROM rhi_points'):
            ids.add(rid)
        for rid in sorted(ids):
            result[rid] = _collect_rhi(conn, rid)
        return result


def get_kri(rhi_id: str) -> Dict[str, Any]:
    with get_conn() as conn:
        return _collect_rhi(conn, rhi_id)

