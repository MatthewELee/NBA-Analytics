"""Fake sources for tests. Column names follow nba_api's expected_data for each endpoint;
ESPN payloads follow the public site API's shape. Players and stats are made up."""

from __future__ import annotations

from datetime import date

BOS, NYK, GSW, LAL = 1610612738, 1610612752, 1610612744, 1610612747


def _set(name, headers, rows):
    return {"name": name, "headers": headers, "rowSet": rows}


PLAYER_INDEX_HEADERS = [
    "PERSON_ID", "PLAYER_LAST_NAME", "PLAYER_FIRST_NAME", "PLAYER_SLUG", "TEAM_ID", "TEAM_SLUG", "IS_DEFUNCT",
    "TEAM_CITY", "TEAM_NAME", "TEAM_ABBREVIATION", "JERSEY_NUMBER", "POSITION", "HEIGHT", "WEIGHT", "COLLEGE",
    "COUNTRY", "DRAFT_YEAR", "DRAFT_ROUND", "DRAFT_NUMBER", "ROSTER_STATUS", "PTS", "REB", "AST",
    "STATS_TIMEFRAME", "FROM_YEAR", "TO_YEAR",
]

PLAYERS = [
    # id, last, first, team, jersey, pos, height, weight, draft (year, round, number), from, to
    (9000001, "Okafor-Reyes", "Jalen", BOS, "7", "G", "6-4", "205", (2017, 1, 3), 2017, 2026),
    (9000002, "Lindqvist", "Mats", NYK, "23", "F-C", "6-11", "245", (2015, 1, 12), 2015, 2026),
    (9000003, "Baptiste", "Dorian", GSW, "1", "G-F", "6-7", "215", (None, None, None), 2019, 2026),
]


def player_index_rows():
    out = []
    for pid, last, first, team, jersey, pos, h, w, (dy, dr, dn), fy, ty in PLAYERS:
        out.append([pid, last, first, None, team, None, "N", None, None, None, jersey, pos, h, w, None, "USA",
                    dy, dr, dn, 1, 20.1, 5.2, 4.1, "Season", str(fy), str(ty)])
    return out


BASE_HEADERS = ["PLAYER_ID", "PLAYER_NAME", "TEAM_ID", "TEAM_ABBREVIATION", "AGE", "GP", "W", "L", "W_PCT", "MIN",
                "FGM", "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT", "FTM", "FTA", "FT_PCT", "OREB", "DREB", "REB",
                "AST", "TOV", "STL", "BLK", "BLKA", "PF", "PFD", "PTS", "PLUS_MINUS"]
ADV_HEADERS = ["PLAYER_ID", "PLAYER_NAME", "TEAM_ID", "TEAM_ABBREVIATION", "AGE", "GP", "OFF_RATING", "DEF_RATING",
               "NET_RATING", "EFG_PCT", "TS_PCT", "USG_PCT", "PACE", "PIE"]


def base_rows(season):
    bump = int(season[:4]) - 2024
    return [
        [9000001, "Jalen Okafor-Reyes", BOS, "BOS", 26.0, 70, 50, 20, .714, 2450.5, 700 + bump, 1400, .5, 200, 520,
         .385, 400, 460, .87, 60, 300, 360, 450, 210, 80, 30, 40, 150, 380, 2000 + 10 * bump, 300],
        [9000002, "Mats Lindqvist", NYK, "NYK", 31.0, 65, 40, 25, .615, 2100.0, 520, 1000, .52, 80, 230, .348, 250,
         300, .833, 160, 520, 680, 190, 140, 50, 90, 30, 170, 260, 1370, 120],
        [9000003, "Dorian Baptiste", GSW, "GSW", 27.0, 72, 45, 27, .625, 2300.0, 600, 1250, .48, 180, 480, .375, 300,
         350, .857, 70, 330, 400, 320, 160, 70, 40, 35, 160, 300, 1680, 90],
        # Not in the players table: should be skipped, not fail the run.
        [9999999, "Unknown Player", LAL, "LAL", 22.0, 5, 1, 4, .2, 40.0, 5, 12, .417, 1, 4, .25, 2, 2, 1.0, 1, 3,
         4, 2, 1, 0, 0, 0, 3, 2, 13, -10],
    ]


def adv_rows(season):
    return [
        [9000001, "Jalen Okafor-Reyes", BOS, "BOS", 26.0, 70, 118.2, 108.1, 10.1, .571, .612, .318, 99.1, .182],
        [9000002, "Mats Lindqvist", NYK, "NYK", 31.0, 65, 114.0, 109.5, 4.5, .56, .6, .22, 97.4, .13],
        [9000003, "Dorian Baptiste", GSW, "GSW", 27.0, 72, 115.0, 111.0, 4.0, .552, .589, .265, 100.2, .14],
    ]


LOG_HEADERS = ["SEASON_ID", "TEAM_ID", "TEAM_ABBREVIATION", "TEAM_NAME", "GAME_ID", "GAME_DATE", "MATCHUP", "WL",
               "MIN", "FGM", "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT", "FTM", "FTA", "FT_PCT", "OREB", "DREB",
               "REB", "AST", "STL", "BLK", "TOV", "PF", "PTS", "PLUS_MINUS", "VIDEO_AVAILABLE"]


def team_log_rows():
    return [
        ["22026", BOS, "BOS", "Boston Celtics", "0022600001", "2026-10-21", "BOS vs. NYK", "W", 240, 44, 88, .5,
         15, 38, .395, 15, 18, .833, 9, 36, 45, 27, 8, 5, 12, 18, 118, 14],
        ["22026", NYK, "NYK", "New York Knicks", "0022600001", "2026-10-21", "NYK @ BOS", "L", 240, 40, 90, .444,
         10, 33, .303, 14, 19, .737, 11, 31, 42, 22, 6, 3, 14, 20, 104, -14],
        ["22026", GSW, "GSW", "Golden State Warriors", "0022600002", "2026-10-22", "GSW @ LAL", "L", 240, 38, 87,
         .437, 13, 40, .325, 10, 12, .833, 8, 33, 41, 25, 7, 4, 13, 19, 99, -8],
        ["22026", LAL, "LAL", "Los Angeles Lakers", "0022600002", "2026-10-22", "LAL vs. GSW", "W", 240, 42, 85,
         .494, 9, 28, .321, 14, 17, .824, 10, 38, 48, 26, 8, 6, 11, 16, 107, 8],
    ]


def player_log_rows():
    headers = ["SEASON_ID", "PLAYER_ID", "PLAYER_NAME", *LOG_HEADERS[1:]]
    rows = [
        ["22026", 9000001, "Jalen Okafor-Reyes", BOS, "BOS", "Boston Celtics", "0022600001", "2026-10-21",
         "BOS vs. NYK", "W", 36, 13, 23, .565, 5, 11, .455, 10, 11, .909, 1, 6, 7, 9, 2, 0, 3, 2, 41, 14],
        ["22026", 9000002, "Mats Lindqvist", NYK, "NYK", "New York Knicks", "0022600001", "2026-10-21",
         "NYK @ BOS", "L", 34, 8, 15, .533, 1, 3, .333, 4, 4, 1.0, 3, 9, 12, 3, 1, 2, 2, 3, 21, -10],
    ]
    return headers, rows


STANDINGS_HEADERS = ["LeagueID", "SeasonID", "TeamID", "TeamCity", "TeamName", "Conference", "PlayoffRank",
                     "Division", "DivisionRank", "WINS", "LOSSES", "LeagueRank", "HOME", "ROAD", "L10",
                     "strCurrentStreak", "ConferenceGamesBack", "PointsPG", "OppPointsPG"]


def standings_rows():
    return [
        ["00", "22026", BOS, "Boston", "Celtics", "East", 1, "Atlantic", 1, 1, 0, 1, "1-0", "0-0", "1-0", "W 1",
         0.0, 118.0, 104.0],
        ["00", "22026", NYK, "New York", "Knicks", "East", 9, "Atlantic", 3, 0, 1, 25, "0-0", "0-1", "0-1", "L 1",
         1.0, 104.0, 118.0],
        ["00", "22026", GSW, "Golden State", "Warriors", "West", 10, "Pacific", 4, 0, 1, 26, "0-0", "0-1", "0-1",
         "L 1", 1.0, 99.0, 107.0],
        ["00", "22026", LAL, "Los Angeles", "Lakers", "West", 2, "Pacific", 1, 1, 0, 2, "1-0", "0-0", "1-0", "W 1",
         0.0, 107.0, 99.0],
    ]


TEAM_ADV_HEADERS = ["TEAM_ID", "TEAM_NAME", "GP", "W", "L", "OFF_RATING", "DEF_RATING", "NET_RATING", "PACE"]


def team_adv_rows():
    return [[BOS, "Boston Celtics", 1, 1, 0, 121.5, 107.0, 14.5, 97.0],
            [NYK, "New York Knicks", 1, 0, 1, 107.0, 121.5, -14.5, 97.0],
            [GSW, "Golden State Warriors", 1, 0, 1, 101.0, 109.2, -8.2, 98.0],
            [LAL, "Los Angeles Lakers", 1, 1, 0, 109.2, 101.0, 8.2, 98.0]]


SCHEDULE_HEADERS = ["gameId", "gameStatus", "gameStatusText", "gameDateEst", "gameDateTimeUTC", "postponedStatus",
                    "homeTeam_teamId", "homeTeam_score", "awayTeam_teamId", "awayTeam_score"]


def schedule_rows():
    return [
        {"gameId": "0022600001", "gameStatus": 3, "gameStatusText": "Final", "gameDateEst": "2026-10-21T00:00:00Z",
         "gameDateTimeUTC": "2026-10-21T23:30:00Z", "postponedStatus": "N", "homeTeam_teamId": BOS,
         "homeTeam_score": 118, "awayTeam_teamId": NYK, "awayTeam_score": 104},
        {"gameId": "0022600050", "gameStatus": 1, "gameStatusText": "7:30 pm ET", "gameDateEst": "2026-10-30T00:00:00Z",
         "gameDateTimeUTC": "2026-10-30T23:30:00Z", "postponedStatus": "N", "homeTeam_teamId": NYK,
         "homeTeam_score": 0, "awayTeam_teamId": BOS, "awayTeam_score": 0},
        # TBD slot, no teams yet: skipped.
        {"gameId": "0062600001", "gameStatus": 1, "gameStatusText": "TBD", "gameDateEst": "2026-12-16T00:00:00Z",
         "gameDateTimeUTC": None, "postponedStatus": "N", "homeTeam_teamId": 0, "homeTeam_score": 0,
         "awayTeam_teamId": 0, "awayTeam_score": 0},
    ]


AWARD_HEADERS = ["PERSON_ID", "FIRST_NAME", "LAST_NAME", "TEAM", "DESCRIPTION", "ALL_NBA_TEAM_NUMBER", "SEASON",
                 "MONTH", "WEEK", "CONFERENCE", "TYPE", "SUBTYPE1", "SUBTYPE2", "SUBTYPE3"]


class FakeNba:
    """Stands in for sources.nba.NbaStats, returning parsed rows like the real one."""

    def player_index(self, season, historical=False):
        return [dict(zip(PLAYER_INDEX_HEADERS, r)) for r in player_index_rows()]

    def player_stats(self, season, measure="Base", season_type="Regular Season"):
        if measure == "Advanced":
            return [dict(zip(ADV_HEADERS, r)) for r in adv_rows(season)]
        return [dict(zip(BASE_HEADERS, r)) for r in base_rows(season)]

    def team_stats(self, season, measure="Base", season_type="Regular Season"):
        return [dict(zip(TEAM_ADV_HEADERS, r)) for r in team_adv_rows()]

    def game_log(self, season, who="P", season_type="Regular Season"):
        if who == "T":
            return [dict(zip(LOG_HEADERS, r)) for r in team_log_rows()]
        headers, rows = player_log_rows()
        return [dict(zip(headers, r)) for r in rows]

    def standings(self, season):
        return [dict(zip(STANDINGS_HEADERS, r)) for r in standings_rows()]

    def schedule(self, season):
        return schedule_rows()

    def player_awards(self, player_id):
        if player_id != 9000001:
            return []
        rows = [
            [9000001, "Jalen", "Okafor-Reyes", "Boston Celtics", "NBA All-Star", None, "2025-26", None, None, "East",
             "Award", None, None, None],
            [9000001, "Jalen", "Okafor-Reyes", "Boston Celtics", "All-NBA", "1", "2025-26", None, None, None,
             "Award", None, None, None],
            [9000001, "Jalen", "Okafor-Reyes", "Boston Celtics", "NBA Player of the Week", None, "2025-26", None,
             "20260112", "East", "Award", None, None, None],
        ]
        return [dict(zip(AWARD_HEADERS, r)) for r in rows]


def espn_competitor(home_away, abbr, score):
    return {"homeAway": home_away, "score": str(score), "team": {"abbreviation": abbr}}


class FakeEspn:
    def teams(self):
        return {"sports": [{"leagues": [{"teams": [
            {"team": {"id": "2", "abbreviation": "BOS", "color": "008348", "alternateColor": "ffffff",
                      "logos": [{"href": "https://a.espncdn.com/i/teamlogos/nba/500/bos.png"}]}},
            {"team": {"id": "18", "abbreviation": "NY", "color": "1d428a", "alternateColor": "f58426",
                      "logos": [{"href": "https://a.espncdn.com/i/teamlogos/nba/500/ny.png"}]}},
            {"team": {"id": "9", "abbreviation": "GS", "color": "fdb927", "alternateColor": "1d428a", "logos": []}},
        ]}]}]}

    def scoreboard(self, day: date):
        if day != date(2026, 10, 23):
            return {"events": []}
        return {"events": [
            {"id": "401800001", "date": "2026-10-23T23:00Z",
             "status": {"type": {"state": "in", "name": "STATUS_IN_PROGRESS", "shortDetail": "Q3 4:12"}},
             "competitions": [{"competitors": [espn_competitor("home", "GS", 71), espn_competitor("away", "NY", 68)]}]},
        ]}

    def news(self, limit=50):
        return {"articles": [
            {"id": 47000001, "headline": "Okafor-Reyes drops 41 in opener", "description": "A night to remember.",
             "published": "2026-10-22T03:15:00Z", "byline": "Staff",
             "links": {"web": {"href": "https://www.espn.com/nba/story/_/id/47000001"}},
             "images": [{"url": "https://a.espncdn.com/photo/1.jpg"}],
             "categories": [{"type": "team", "teamId": 2}, {"type": "athlete", "description": "Jalen Okafor-Reyes"}]},
            {"headline": "No link, skipped", "published": "2026-10-22T03:15:00Z"},
        ]}
