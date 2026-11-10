"""SQLite human-review queue. Low-confidence answers and manual escalations land here."""
import json
import sqlite3
import time

from copilot.config import p

SCHEMA = """CREATE TABLE IF NOT EXISTS review_queue (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  question TEXT NOT NULL,
  draft_answer TEXT,
  confidence REAL,
  reasons TEXT,            -- JSON list of gate reasons, or ["user_escalated"]
  sources TEXT,            -- JSON list of retrieved chunk ids
  source TEXT NOT NULL,    -- 'gate' | 'user'
  status TEXT NOT NULL DEFAULT 'open',   -- open | resolved
  reviewer_answer TEXT,
  resolved_at TEXT
)"""


def connect(cfg: dict, db_path=None) -> sqlite3.Connection:
    path = db_path or p(cfg["review_queue"]["db_path"])
    con = sqlite3.connect(path, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute(SCHEMA)
    return con


def enqueue(con, question, draft_answer, confidence, reasons, sources, source="gate") -> int:
    cur = con.execute(
        "INSERT INTO review_queue (created_at, question, draft_answer, confidence, reasons, sources, source)"
        " VALUES (?,?,?,?,?,?,?)",
        (time.strftime("%Y-%m-%d %H:%M:%S"), question, draft_answer, confidence,
         json.dumps(reasons), json.dumps(sources), source))
    con.commit()
    return cur.lastrowid


def list_items(con, status="open"):
    return [dict(r) for r in con.execute(
        "SELECT * FROM review_queue WHERE status=? ORDER BY id DESC", (status,))]


def resolve(con, item_id: int, reviewer_answer: str):
    con.execute("UPDATE review_queue SET status='resolved', reviewer_answer=?, resolved_at=? WHERE id=?",
                (reviewer_answer, time.strftime("%Y-%m-%d %H:%M:%S"), item_id))
    con.commit()
