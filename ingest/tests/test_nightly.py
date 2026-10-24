"""The nightly ESPN path against a real Postgres with fake sources. Needs TEST_DATABASE_URL."""

import os
from decimal import Decimal

import psycopg
import pytest

from bk_ingest.config import Settings
from bk_ingest.db import migrate
from bk_ingest.tasks import Tasks

from . import fakes

URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="TEST_DATABASE_URL not set")

SEASON = "2026-27"


@pytest.fixture(scope="module")
def tasks():
    conn = psycopg.connect(URL)
    with conn.cursor() as cur:
        cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    conn.commit()
    migrate(conn)
    settings = Settings(database_url=URL, nba_api_proxy=None, nba_api_timeout=5, nba_api_delay=0,
                        balldontlie_api_key=None)
    t = Tasks(conn, settings)
    t._nba, t._espn = fakes.FakeNba(), fakes.FakeEspnNight()
    yield t
    conn.close()


def q(t, sql, *args):
    with t.conn.cursor() as cur:
        cur.execute(sql, args)
        return cur.fetchall()


ROOKIE = -5100001


def test_nightly_from_espn(tasks):
    tasks.teams()
    tasks.players(SEASON)
    tasks.espn_schedule(SEASON)
    assert q(tasks, "SELECT espn_id, season_type, status FROM games ORDER BY game_date") == [
        ("401700001", "Pre Season", "final"), ("401800010", "Regular Season", "final"),
        ("401800020", "Regular Season", "final"), ("401800030", "Regular Season", "scheduled")]

    tasks.boxscores(SEASON)
    assert tasks._espn.summaries_fetched == ["401800010", "401800020"]  # no preseason box scores

    # Known players matched by name and given their ESPN id; the rookie gets a placeholder.
    assert q(tasks, "SELECT espn_id FROM players WHERE id = 9000001") == [("3900001",)]
    assert q(tasks, "SELECT slug, full_name, team_id, headshot_url LIKE '%%espncdn%%' FROM players WHERE id < 0") == [
        ("theo-marchetti-jr", "Theo Marchetti Jr.", fakes.BOS, True)]
    assert q(tasks, "SELECT pts, matchup, wl, min, fg3m, fg3a, plus_minus FROM player_games WHERE player_id = 9000001 ORDER BY game_date") == [
        (34, "BOS vs. NYK", "W", Decimal("36.0"), 4, 8, 10), (29, "BOS @ GSW", "W", Decimal("36.0"), 4, 8, 3)]
    assert q(tasks, "SELECT count(*) FROM player_games WHERE player_id = %s", ROOKIE)[0][0] == 2
    assert q(tasks, "SELECT pts, opp_pts, wl, plus_minus FROM team_games WHERE team_id = %s ORDER BY game_date", fakes.NYK) == [
        (110, 120, "L", -10)]

    tasks.rollup(SEASON)
    (gp, pts, ts, efg, usg), = q(tasks, """SELECT gp, pts, ts_pct, efg_pct, usg_pct FROM player_seasons
                                          WHERE player_id = 9000001 AND season = %s""", SEASON)
    assert (gp, pts) == (2, 63)
    assert ts == Decimal(str(round(63 / (2 * (40 + 0.44 * 14)), 3)))
    assert efg == Decimal(str(round((24 + 0.5 * 8) / 40, 3)))
    # Usage: the possessions Jalen used over Boston's while he was on the floor (team minutes / 5).
    used, team_used, team_min = 20 + 0.44 * 7 + 3, (20 + 0.44 * 7 + 3) + (9 + 0.44 * 2 + 1), 36 + 22
    assert usg == Decimal(str(round(used / (36 * team_used / (team_min / 5)), 3)))
    assert q(tasks, """SELECT wins, losses, streak, last_ten, home_record, road_record, conf_rank, games_back
                       FROM team_seasons WHERE team_id = %s AND season = %s""", fakes.BOS, SEASON) == [
        (2, 0, "W 2", "2-0", "1-0", "1-0", 1, Decimal("0.0"))]
    assert q(tasks, "SELECT conf_rank, games_back FROM team_seasons WHERE team_id = %s", fakes.NYK) == [(2, Decimal("1.5"))]
    (ortg, drtg, pace), = q(tasks, "SELECT off_rating, def_rating, pace FROM team_seasons WHERE team_id = %s", fakes.BOS)
    assert ortg > drtg and pace > 0
    tasks.ledger(SEASON)

    # Running again fetches nothing new and changes nothing.
    tasks.espn_schedule(SEASON)
    tasks.boxscores(SEASON)
    assert tasks._espn.summaries_fetched == ["401800010", "401800020"]
    assert q(tasks, "SELECT task, source FROM ingest_runs WHERE NOT ok") == []


def test_placeholder_folds_into_nba_player(tasks):
    # NBA.com now lists the rookie (without the suffix).
    rookie = [9000004, "Marchetti", "Theo", None, fakes.BOS, None, "N", None, None, None, "9", "F", "6-8", "220",
              None, "Italy", 2026, 1, 14, 1, 11.0, 4.0, 2.0, "Season", "2026", "2026"]
    orig = tasks._nba.player_index
    tasks._nba.player_index = lambda season, historical=False: (
        orig(season, historical) + [dict(zip(fakes.PLAYER_INDEX_HEADERS, rookie))])
    try:
        tasks.players(SEASON)
    finally:
        tasks._nba.player_index = orig

    assert q(tasks, "SELECT count(*) FROM players WHERE id < 0")[0][0] == 0
    # The real player keeps the slug the placeholder had, and its ESPN id.
    assert q(tasks, "SELECT slug, espn_id FROM players WHERE id = 9000004") == [("theo-marchetti-jr", "5100001")]
    assert q(tasks, "SELECT count(*) FROM player_games WHERE player_id = 9000004")[0][0] == 2
    tasks.rollup(SEASON)
    assert q(tasks, "SELECT gp, pts FROM player_seasons WHERE player_id = 9000004") == [(2, 22)]
