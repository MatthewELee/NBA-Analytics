"""Runs every task against a real Postgres with fake sources.

Needs TEST_DATABASE_URL pointing at a throwaway database: the public schema is dropped and rebuilt.
"""

import os
from datetime import date
from decimal import Decimal

import psycopg
import pytest

from bk_ingest.config import Settings
from bk_ingest.db import migrate
from bk_ingest.tasks import Tasks

from . import fakes

URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="TEST_DATABASE_URL not set")


@pytest.fixture(scope="module")
def tasks():
    conn = psycopg.connect(URL)
    with conn.cursor() as cur:
        cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    conn.commit()
    assert migrate(conn) == ["001_init.sql", "002_espn_players.sql"]
    assert migrate(conn) == []
    settings = Settings(database_url=URL, nba_api_proxy=None, nba_api_timeout=5, nba_api_delay=0,
                        balldontlie_api_key=None)
    t = Tasks(conn, settings)
    t._nba, t._espn = fakes.FakeNba(), fakes.FakeEspn()
    yield t
    conn.close()


def q(t, sql, *args):
    with t.conn.cursor() as cur:
        cur.execute(sql, args)
        return cur.fetchall()


def test_full_pipeline(tasks):
    assert tasks.teams() == 30
    assert tasks.players("2026-27") == 3
    tasks.standings("2026-27")
    tasks.backfill("2024-25", "2026-27")
    tasks.gamelogs("2026-27")
    tasks.schedule("2026-27")
    tasks.awards()
    tasks.news()

    assert q(tasks, "SELECT color_primary, conference FROM teams WHERE abbr = 'BOS'") == [("008348", "East")]
    assert q(tasks, "SELECT slug, is_active FROM players WHERE id = 9000001") == [("jalen-okafor-reyes", True)]
    # Three seasons of history, the unknown player skipped.
    assert q(tasks, "SELECT count(*) FROM player_seasons WHERE player_id = 9000001")[0][0] == 3
    assert q(tasks, "SELECT count(*) FROM player_seasons WHERE player_id = 9999999")[0][0] == 0
    assert q(tasks, "SELECT pts_pg FROM player_season_averages WHERE player_id = 9000001 AND season = '2026-27'")[0][0] == Decimal("28.9")
    assert q(tasks, "SELECT status, home_score FROM games WHERE id = '0022600001'") == [("final", 118)]
    assert q(tasks, "SELECT status FROM games WHERE id = '0022600050'") == [("scheduled",)]
    assert q(tasks, "SELECT pts FROM player_games WHERE player_id = 9000001") == [(41,)]
    assert q(tasks, "SELECT net_rating FROM team_seasons WHERE team_id = %s", fakes.BOS)[0][0] == Decimal("14.5")
    assert q(tasks, "SELECT count(*) FROM awards")[0][0] == 3
    assert q(tasks, "SELECT player_ids FROM news")[0][0] == [9000001]
    # Re-running is idempotent.
    tasks.awards()
    assert q(tasks, "SELECT count(*) FROM awards")[0][0] == 3
    ok = q(tasks, "SELECT task, ok FROM ingest_runs WHERE NOT ok")
    assert ok == []


def test_scoreboard_placeholder_then_merge(tasks):
    tasks.scoreboard(date(2026, 10, 23))
    assert q(tasks, "SELECT id, status, home_score, status_detail FROM games WHERE espn_id = '401800001'") == [
        ("espn-401800001", "live", 71, "Q3 4:12")]

    # The NBA schedule now carries the same game: the placeholder folds into it.
    real = {"gameId": "0022600010", "gameStatus": 2, "gameStatusText": "Q3 4:12", "gameDateEst": "2026-10-23T00:00:00Z",
            "gameDateTimeUTC": "2026-10-23T23:00:00Z", "postponedStatus": "N", "homeTeam_teamId": fakes.GSW,
            "homeTeam_score": 71, "awayTeam_teamId": fakes.NYK, "awayTeam_score": 68}
    orig = tasks._nba.schedule
    tasks._nba.schedule = lambda season: fakes.schedule_rows() + [real]
    try:
        tasks.schedule("2026-27")
    finally:
        tasks._nba.schedule = orig
    assert q(tasks, "SELECT id FROM games WHERE espn_id = '401800001'") == [("0022600010",)]
    assert q(tasks, "SELECT count(*) FROM games WHERE id LIKE 'espn-%%'")[0][0] == 0

    # Next scoreboard poll updates the real game in place.
    tasks.scoreboard(date(2026, 10, 23))
    assert q(tasks, "SELECT id FROM games WHERE game_date = '2026-10-23'") == [("0022600010",)]


def test_failed_run_is_logged(tasks):
    def boom(*a, **k):
        raise ConnectionError("blocked")

    orig = tasks._nba.standings
    tasks._nba.standings = boom
    try:
        with pytest.raises(ConnectionError):
            tasks.standings("2026-27")
    finally:
        tasks._nba.standings = orig
    assert q(tasks, "SELECT ok, error FROM ingest_runs WHERE task = 'standings' ORDER BY id DESC LIMIT 1") == [
        (False, "ConnectionError: blocked")]
