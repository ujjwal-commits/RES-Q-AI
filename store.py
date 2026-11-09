"""Tiny SQLite store for incident reports.

The database file (data/resq.db) is recreated on every start so the dashboard
always opens empty. To keep reports between runs, start the server with
`python server.py --keep`.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS incidents (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    text        TEXT NOT NULL,
    created_at  REAL NOT NULL,
    status      TEXT NOT NULL DEFAULT 'active',
    score       REAL NOT NULL,
    result      TEXT NOT NULL,
    reported_by TEXT,
    handled_by  TEXT,
    handled_at  REAL
)
"""


class Store:
    def __init__(self, path: Path, fresh: bool = True):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if fresh and path.exists():
            try:
                path.unlink()
            except OSError:
                pass
        self.lock = threading.Lock()
        self.conn = sqlite3.connect(str(path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        with self.lock:
            self.conn.execute(SCHEMA)
            self.conn.commit()

    @staticmethod
    def _to_dict(row):
        d = json.loads(row["result"])
        d.update({
            "id": row["id"], "text": row["text"], "created_at": row["created_at"], "status": row["status"],
            "reported_by": row["reported_by"], "handled_by": row["handled_by"], "handled_at": row["handled_at"],
        })
        return d

    def add(self, text: str, result: dict, created_at: float | None = None, reported_by: str | None = None) -> dict:
        created_at = created_at if created_at is not None else time.time()
        with self.lock:
            cur = self.conn.execute(
                "INSERT INTO incidents (text, created_at, status, score, result, reported_by) VALUES (?, ?, 'active', ?, ?, ?)",
                (text, created_at, result["score"], json.dumps(result), reported_by),
            )
            self.conn.commit()
            row = self.conn.execute("SELECT * FROM incidents WHERE id = ?", (cur.lastrowid,)).fetchone()
        return self._to_dict(row)

    def active(self) -> list:
        """Active incidents, most urgent first; older reports win ties."""
        with self.lock:
            rows = self.conn.execute(
                "SELECT * FROM incidents WHERE status = 'active' ORDER BY score DESC, created_at ASC"
            ).fetchall()
        return [self._to_dict(r) for r in rows]

    def everything(self) -> list:
        with self.lock:
            rows = self.conn.execute("SELECT * FROM incidents ORDER BY created_at ASC").fetchall()
        return [self._to_dict(r) for r in rows]

    def resolve(self, incident_id: int, handled_by: str | None = None) -> bool:
        with self.lock:
            cur = self.conn.execute(
                "UPDATE incidents SET status = 'handled', handled_by = ?, handled_at = ? WHERE id = ? AND status = 'active'",
                (handled_by, time.time(), incident_id),
            )
            self.conn.commit()
            return cur.rowcount > 0

    def recent_handled(self, limit: int = 8) -> list:
        with self.lock:
            rows = self.conn.execute(
                "SELECT * FROM incidents WHERE status = 'handled' ORDER BY handled_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [self._to_dict(r) for r in rows]

    def handled_count(self) -> int:
        with self.lock:
            return self.conn.execute("SELECT COUNT(*) FROM incidents WHERE status = 'handled'").fetchone()[0]

    def clear(self):
        with self.lock:
            self.conn.execute("DELETE FROM incidents")
            self.conn.commit()
