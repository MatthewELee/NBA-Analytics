"""Ledger detection against a real Postgres. Needs TEST_DATABASE_URL (the schema is rebuilt)."""

import os
from datetime import date, timedelta

import psycopg
import pytest

from bk_ingest import ledger
from bk_ingest.db import migrate, upsert

URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="TEST_DATABASE_URL not set")

SEASON = "2026-27"
OPENER = date(2026, 10, 20)


def player(pid, name, active, from_year, team_id=1610612744):
    first, last = name.split(" ", 1)
    return {"id": pid, "slug": name.lower().replace(" ", "-"), "first_name": first, "last_name": last,
            "full_name": name, "team_id": team_id if active else None, "is_active": active, "from_year": from_year}


def season_row(pid, season, pts, gp=70, **kw):
    return {"player_id": pid, "season": season, "season_type": "Regular Season", "team_id": 0, "gp": gp,
            "pts": pts, "reb": kw.get("reb", 300), "ast": kw.get("ast", 200), "stl": 50, "blk": 20, "fg3m": 100}


@pytest.fixture()
def conn():
    c = psycopg.connect(URL)
    try:
        yield _seed(c)
    finally:
        c.close()


def _seed(c):
    with c.cursor() as cur:
        cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    c.commit()
    migrate(c)
    upsert(c, "teams", [
        {"id": 1610612744, "abbr": "GSW", "city": "Golden State", "name": "Warriors", "full_name": "Golden State Warriors"},
        {"id": 1610612747, "abbr": "LAL", "city": "Los Angeles", "name": "Lakers", "full_name": "Los Angeles Lakers"},
    ], ["id"])
    upsert(c, "players", [
        player(1, "Ada Hoops", True, 2018),        # full history loaded
        player(2, "Old Timer", False, 2000),       # retired, 9,990 career points
        player(3, "Missing Years", True, 2010),    # only one earlier season loaded
        player(4, "Rookie Star", True, 2026),
    ], ["id"])
    upsert(c, "player_seasons", [
        *[season_row(1, f"{y}-{str(y + 1)[-2:]}", 1240) for y in range(2018, 2026)],  # 9,920
        *[season_row(2, f"{y}-{str(y + 1)[-2:]}", 999) for y in range(2000, 2010)],   # 9,990
        season_row(3, "2025-26", 9_950),
    ], ["player_id", "season", "season_type", "team_id"])
    games, logs = [], []
    for i in range(4):
        day = OPENER + timedelta(days=2 * i)
        gid = f"00226000{i}"
        games.append({"id": gid, "season": SEASON, "game_date": day, "home_team_id": 1610612744,
                      "away_team_id": 1610612747, "home_score": 110, "away_score": 100, "status": "final"})
        for pid, pts in ((1, 30), (3, 30), (4, [20, 41, 38, 44][i])):
            logs.append({"player_id": pid, "game_id": gid, "season": SEASON, "game_date": day,
                         "team_id": 1610612744, "matchup": "GSW vs. LAL", "min": 34, "pts": pts, "reb": 5,
                         "ast": 5, "stl": 1, "blk": 0, "fg3m": 2})
    upsert(c, "games", games, ["id"])
    upsert(c, "player_games", logs, ["player_id", "game_id"])
    upsert(c, "awards", [
        {"player_id": 4, "award": "NBA Player of the Week", "season": SEASON, "week": "2026-10-26",
         "conference": "West", "source": "NBA.com"},
        {"player_id": 1, "award": "NBA All-Star", "season": "2025-26", "week": None, "conference": None,
         "source": "NBA.com"},  # last season: skipped
    ], ["player_id", "award", "season", "team_label", "month", "week"])
    c.commit()
    return c


def items(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT kind, headline, detail, occurred_on, player_id FROM ledger_items ORDER BY occurred_on, id")
        return cur.fetchall()


def test_detects_each_kind_once(conn):
    added = ledger.detect(conn, SEASON)
    found = items(conn)
    assert added == len(found)
    heads = [h for _, h, *_ in found]

    # 9,920 + 30 + 30 + 30 crosses 10,000 in the third game, passing Old Timer (9,990) in the third too.
    assert ("milestone", "Ada Hoops passes 10,000 career points", "Reached 10,010 against LAL.",
            OPENER + timedelta(days=4), 1) in found
    assert "Ada Hoops passes Old Timer in career points" in heads
    # History before 2025-26 isn't loaded, so no milestone that may be years old.
    assert not any(pid == 3 for *_, pid in found)
    # Season highs only when the game beats every earlier one and the floor (40 points).
    assert [h for h in heads if "season high" in h] == [
        "Rookie Star scores 41 points, the season high",
        "Rookie Star scores 44 points, the season high",
    ]
    assert "Rookie Star is named Western Conference Player of the Week" in heads
    assert not any("All-Star" in h for h in heads)

    assert ledger.detect(conn, SEASON) == 0
    assert len(items(conn)) == len(found)
