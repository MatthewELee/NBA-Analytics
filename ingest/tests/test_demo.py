"""The demo seeder fills an empty database and labels every row it writes as demo data."""

import os
from datetime import date

import psycopg
import pytest

from bk_ingest import demo
from bk_ingest.db import migrate

URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="TEST_DATABASE_URL not set")


def test_seed_is_repeatable():
    with psycopg.connect(URL) as conn:
        with conn.cursor() as cur:
            cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
        migrate(conn)
        first = demo.seed(conn, date(2026, 11, 20))
        again = demo.seed(conn, date(2026, 11, 20))
        assert first == again
        assert first["players"] == 30 * 13
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM players")
            assert cur.fetchone()[0] == first["players"]
            cur.execute("SELECT count(*) FROM games WHERE status = 'final' AND game_date >= %s", (date(2026, 11, 20),))
            assert cur.fetchone()[0] == 0
            cur.execute("SELECT DISTINCT source FROM ingest_runs")
            assert all("Demo" in s for (s,) in cur.fetchall())
        conn.rollback()
