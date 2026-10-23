from datetime import date

from bk_ingest import transforms as t
from bk_ingest.config import season_for
from bk_ingest.util import slugify, to_date

from . import fakes


def test_season_for():
    assert season_for(date(2026, 10, 23)) == "2026-27"
    assert season_for(date(2027, 4, 1)) == "2026-27"
    assert season_for(date(2027, 9, 30)) == "2026-27"


def test_slugify_strips_accents():
    assert slugify("Luka Dončić") == "luka-doncic"
    assert slugify("Shai Gilgeous-Alexander") == "shai-gilgeous-alexander"


def test_to_date_formats():
    assert to_date("2026-10-21") == date(2026, 10, 21)
    assert to_date("2026-10-21T00:00:00") == date(2026, 10, 21)
    assert to_date("OCT 21, 2026") == date(2026, 10, 21)
    assert to_date("10/21/2026 00:00:00") == date(2026, 10, 21)
    assert to_date("") is None


def test_player_rows_keeps_existing_slug_and_resolves_clash():
    index = fakes.FakeNba().player_index("2026-27")
    rows = t.player_rows(index, existing_slugs={9000002: "mats-lindqvist-old"})
    by_id = {r["id"]: r for r in rows}
    assert by_id[9000002]["slug"] == "mats-lindqvist-old"
    assert by_id[9000001]["slug"] == "jalen-okafor-reyes"
    assert by_id[9000003]["draft_year"] is None and by_id[9000003]["draft_round"] is None

    clash = t.player_rows(index, existing_slugs={1: "jalen-okafor-reyes"})
    assert {r["id"]: r for r in clash}[9000001]["slug"] == "jalen-okafor-reyes-9000001"


def test_player_season_rows_merges_advanced():
    nba = fakes.FakeNba()
    rows = t.player_season_rows(nba.player_stats("2026-27"), nba.player_stats("2026-27", "Advanced"),
                                "2026-27", "Regular Season")
    r = next(x for x in rows if x["player_id"] == 9000001)
    assert r["pts"] == 2020 and r["gp"] == 70 and r["min"] == 2450.5
    assert r["ts_pct"] == 0.612 and r["team_id"] == 0 and r["team_abbr"] == "BOS"


def test_games_from_team_log_pairs_home_and_away():
    log = fakes.FakeNba().game_log("2026-27", "T")
    games = {g["id"]: g for g in t.games_from_team_log(log, "2026-27", "Regular Season")}
    g = games["0022600001"]
    assert (g["home_team_id"], g["away_team_id"]) == (fakes.BOS, fakes.NYK)
    assert (g["home_score"], g["away_score"]) == (118, 104)


def test_team_game_rows_opponent_points():
    rows = t.team_game_rows(fakes.FakeNba().game_log("2026-27", "T"), "2026-27", "Regular Season")
    nyk = next(r for r in rows if r["team_id"] == fakes.NYK)
    assert nyk["opp_pts"] == 118


def test_schedule_skips_tbd_and_hides_scheduled_scores():
    rows = t.games_from_schedule(fakes.schedule_rows(), "2026-27")
    assert [r["id"] for r in rows] == ["0022600001", "0022600050"]
    upcoming = rows[1]
    assert upcoming["status"] == "scheduled" and upcoming["home_score"] is None
    assert upcoming["game_date"] == date(2026, 10, 30)


def test_scoreboard_maps_espn_abbreviations_and_et_date():
    teams = {"GSW": fakes.GSW, "NYK": fakes.NYK}
    rows = t.scoreboard_rows(fakes.FakeEspn().scoreboard(date(2026, 10, 23)), teams, "2026-27")
    assert len(rows) == 1
    r = rows[0]
    assert (r["home_team_id"], r["away_team_id"]) == (fakes.GSW, fakes.NYK)
    assert r["status"] == "live" and r["home_score"] == 71
    assert r["game_date"] == date(2026, 10, 23)  # 23:00Z is 7pm ET the same day


def test_news_rows_tags_teams_and_players():
    rows = t.news_rows(fakes.FakeEspn().news(), {"2": fakes.BOS}, {"jalen okafor-reyes": 9000001})
    assert len(rows) == 1
    assert rows[0]["team_ids"] == [fakes.BOS] and rows[0]["player_ids"] == [9000001]


def test_award_rows():
    rows = t.award_rows(fakes.FakeNba().player_awards(9000001), "NBA.com")
    assert {r["award"] for r in rows} == {"NBA All-Star", "All-NBA", "NBA Player of the Week"}
    potw = next(r for r in rows if r["award"] == "NBA Player of the Week")
    assert potw["week"] == "2026-01-12"


def test_teams_rows_branding():
    rows = {r["abbr"]: r for r in t.teams_rows(fakes_static(), fakes.FakeEspn().teams())}
    assert rows["NYK"]["espn_id"] == "18" and rows["NYK"]["color_primary"] == "1d428a"
    assert rows["LAL"]["espn_id"] is None and rows["LAL"]["logo_url"].endswith("/logo.svg")


def fakes_static():
    from nba_api.stats.static import teams

    return teams.get_teams()
