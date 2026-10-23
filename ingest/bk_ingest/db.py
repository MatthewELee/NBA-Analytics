"""Postgres access: connections, upserts, run logging and migrations."""

from __future__ import annotations

import contextlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Sequence

import psycopg

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "db" / "migrations"


def connect(url: str) -> psycopg.Connection:
    return psycopg.connect(url, autocommit=False)


def upsert(
    conn: psycopg.Connection,
    table: str,
    rows: Sequence[dict],
    conflict: Sequence[str],
    update: Sequence[str] | None = None,
) -> int:
    """INSERT ... ON CONFLICT DO UPDATE for a list of dicts sharing the same keys."""
    if not rows:
        return 0
    cols = list(rows[0].keys())
    if update is None:
        update = [c for c in cols if c not in conflict]
    col_sql = ", ".join(cols)
    val_sql = ", ".join(f"%({c})s" for c in cols)
    set_sql = ", ".join(f"{c} = EXCLUDED.{c}" for c in update)
    if "updated_at" not in cols and table in _HAS_UPDATED_AT:
        set_sql += (", " if set_sql else "") + "updated_at = now()"
    action = f"DO UPDATE SET {set_sql}" if set_sql else "DO NOTHING"
    sql = f"INSERT INTO {table} ({col_sql}) VALUES ({val_sql}) ON CONFLICT ({', '.join(conflict)}) {action}"
    with conn.cursor() as cur:
        cur.executemany(sql, rows)
    return len(rows)


_HAS_UPDATED_AT = {"teams", "players", "player_seasons", "games", "team_seasons"}


@contextlib.contextmanager
def logged_run(conn: psycopg.Connection, task: str, source: str, season: str | None = None) -> Iterator[dict]:
    """Records a task in ingest_runs. The body sets counter['rows']; failures are logged and re-raised."""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO ingest_runs (task, source, season) VALUES (%s, %s, %s) RETURNING id",
            (task, source, season),
        )
        run_id = cur.fetchone()[0]
    conn.commit()
    counter = {"rows": 0, "source": source}
    try:
        yield counter
        conn.commit()
        _finish(conn, run_id, True, counter["rows"], None, counter["source"])
    except Exception as exc:  # noqa: BLE001 - logged, then re-raised
        conn.rollback()
        _finish(conn, run_id, False, counter["rows"], f"{type(exc).__name__}: {exc}"[:2000], counter["source"])
        raise


def _finish(conn, run_id, ok, rows_written, error, source):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE ingest_runs SET finished_at = %s, ok = %s, rows_written = %s, error = %s, source = %s WHERE id = %s",
            (datetime.now(timezone.utc), ok, rows_written, error, source, run_id),
        )
    conn.commit()


def migrate(conn: psycopg.Connection) -> list[str]:
    """Applies db/migrations/*.sql in name order, once each."""
    with conn.cursor() as cur:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations (name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
        )
        cur.execute("SELECT name FROM schema_migrations")
        done = {r[0] for r in cur.fetchall()}
    conn.commit()
    applied = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if path.name in done:
            continue
        with conn.cursor() as cur:
            cur.execute(path.read_text())
            cur.execute("INSERT INTO schema_migrations (name) VALUES (%s)", (path.name,))
        conn.commit()
        applied.append(path.name)
    return applied
