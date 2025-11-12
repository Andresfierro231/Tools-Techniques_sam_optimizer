from __future__ import annotations
import sqlite3, json, time, pathlib

"""
Persistent run database.
Responsibilities:

Manages a simple SQLite file results/samopt.sqlite.

insert_run(record) appends a row describing one execution.

Enables later querying/plotting of runtime trends or validation metrics.
"""

DB_PATH = pathlib.Path("results/samopt.sqlite")

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs(
  run_id TEXT PRIMARY KEY,
  phase TEXT,
  sam_input_hash TEXT,
  params TEXT,
  features TEXT,
  status TEXT,
  metrics TEXT,
  t_start REAL,
  t_end REAL,
  artifacts_dir TEXT,
  stdout_path TEXT,
  stderr_path TEXT,
  notes TEXT
);
"""

def _json_dump(v):
    return json.dumps(v) if isinstance(v, (dict, list)) else v

def ensure_db(db_path=DB_PATH):
    db_path = pathlib.Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_path))
    con.execute(SCHEMA)
    con.commit()
    return con

def insert_run(record: dict, db_path=DB_PATH):
    con = ensure_db(db_path)
    record.setdefault("t_end", time.time())
    cols = ",".join(record.keys())
    vals = ",".join(["?"]*len(record))
    con.execute(f"INSERT INTO runs ({cols}) VALUES ({vals})",
                tuple(_json_dump(v) for v in record.values()))
    con.commit()
    con.close()

def recent(n=10, db_path=DB_PATH):
    con = ensure_db(db_path)
    cur = con.execute("SELECT run_id, phase, status, t_end, notes FROM runs ORDER BY t_end DESC LIMIT ?", (n,))
    rows = cur.fetchall()
    con.close()
    return rows
