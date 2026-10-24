"""Demo data: fictional players and games so the site can be developed without the live sources.

Never run this against the production database. Everything it writes is made up, and every
ingest run it logs says so in its source, which the site shows on each data view.
"""

from __future__ import annotations

import math
import random
from datetime import date, datetime, time, timedelta, timezone

import psycopg

from . import ledger
from . import transforms as t
from .db import upsert
from .sources import nba

SOURCE = "Demo data (fictional players)"
SEASON = "2026-27"
FIRST_ID = 9_100_000

FIRST = ["Amari", "Bastian", "Cormac", "Dashiell", "Emeka", "Florian", "Gideon", "Hollis", "Idris", "Jovan",
         "Kasimir", "Lucan", "Marlon", "Nikolai", "Osric", "Percival", "Quill", "Rafferty", "Soren", "Tobias",
         "Ulric", "Vaughn", "Wendell", "Xavi", "Yannick", "Zoltan", "Anselm", "Bram", "Caspian", "Darragh"]
LAST = ["Abernathy", "Blackwood", "Castellanos", "Delacroix", "Esterhazy", "Fairweather", "Galloway", "Hargreave",
        "Ishikawa", "Jablonski", "Kowalczyk", "Lindqvist", "Mwangi-Hart", "Nakashima", "Okonkwo-Bell", "Pemberton",
        "Quarshie", "Rasmussen", "Szabo", "Thistlewood", "Underhill", "Vasquez-Moore", "Wainwright", "Yildirim",
        "Zielinski", "Ashworth", "Brannigan", "Cheswick", "Drummond-Kay", "Eriksen"]
POSITIONS = ["G", "G", "G-F", "F", "F", "F-C", "C", "G", "F", "G-F", "C", "F", "G"]
COLORS = ["1d428a", "008348", "ce1141", "552583", "fdb927", "006bb6", "e03a3e", "0e2240", "00788c", "c8102e"]


def _retired_marks(conn: psycopg.Connection, rng: random.Random) -> None:
    """Retired players whose career totals today's stars pass this season, and one big night.

    Gives the demo Ledger some records to show. Every name is still fictional.
    """
    with conn.cursor() as cur:
        cur.execute(
            """SELECT ps.player_id, sum(ps.pts) FILTER (WHERE ps.season < %(s)s),
                      (SELECT sum(pts) FROM player_games g WHERE g.player_id = ps.player_id AND g.season = %(s)s)
               FROM player_seasons ps WHERE ps.team_id = 0 AND ps.player_id < %(retired)s
               GROUP BY ps.player_id ORDER BY 2 DESC NULLS LAST LIMIT 4""",
            {"s": SEASON, "retired": FIRST_ID + 5000},
        )
        marks = cur.fetchall()
    retired, seasons = [], []
    for i, (_, prior, gained) in enumerate(marks):
        pid = FIRST_ID + 5000 + i
        first, last = rng.choice(FIRST), rng.choice(LAST)
        retired.append({
            "PERSON_ID": pid, "PLAYER_FIRST_NAME": first, "PLAYER_LAST_NAME": last, "PLAYER_SLUG": None,
            "TEAM_ID": None, "POSITION": "F", "HEIGHT": "6-8", "COUNTRY": "Demo",
            "FROM_YEAR": 1998, "TO_YEAR": 2012, "ROSTER_STATUS": 0,
        })
        target = int(prior) + int(gained or 0) // 2
        years = list(range(1998, 2013))
        for j, year in enumerate(years):
            pts = target // len(years) + (target % len(years) if j == 0 else 0)
            seasons.append({
                "player_id": pid, "season": f"{year}-{str(year + 1)[-2:]}", "season_type": "Regular Season",
                "team_id": 0, "gp": 75, "pts": pts, "reb": rng.randint(250, 700), "ast": rng.randint(120, 500),
                "stl": rng.randint(40, 120), "blk": rng.randint(10, 90), "fg3m": rng.randint(10, 150),
            })
    with conn.cursor() as cur:
        cur.execute("SELECT id, slug FROM players")
        existing = dict(cur.fetchall())
    upsert(conn, "players", t.player_rows(retired, existing), ["id"])
    upsert(conn, "player_seasons", seasons, ["player_id", "season", "season_type", "team_id"])
    # One night worth writing about.
    with conn.cursor() as cur:
        cur.execute(
            """UPDATE player_games SET pts = 47, fgm = 17, fga = 29 WHERE (player_id, game_id) = (
                 SELECT player_id, game_id FROM player_games WHERE season = %s AND player_id = %s
                 ORDER BY game_date DESC LIMIT 1 OFFSET 2)""",
            (SEASON, marks[0][0] if marks else 0),
        )


def seed(conn: psycopg.Connection, today: date) -> dict:
    rng = random.Random(7)
    static = nba.NbaStats.teams()
    teams = t.teams_rows(static)
    for i, team in enumerate(teams):
        team["color_primary"] = COLORS[i % len(COLORS)]
    upsert(conn, "teams", teams, ["id"])
    conf = {r["id"]: ("East" if i % 2 == 0 else "West") for i, r in enumerate(teams)}
    with conn.cursor() as cur:
        cur.executemany("UPDATE teams SET conference = %s, division = %s WHERE id = %s",
                        [(c, "Demo", tid) for tid, c in conf.items()])

    # ---- players: 13 per team, each with a talent level and a career arc
    players, skill = [], {}
    pid = FIRST_ID
    used = set()
    for team in teams:
        for slot in range(13):
            while True:
                first, last = rng.choice(FIRST), rng.choice(LAST)
                if (first, last) not in used:
                    used.add((first, last))
                    break
            age = rng.randint(20, 35)
            from_year = 2026 - (age - 20) - rng.randint(0, 1)
            drafted = rng.random() > 0.15
            players.append({
                "PERSON_ID": pid, "PLAYER_FIRST_NAME": first, "PLAYER_LAST_NAME": last, "PLAYER_SLUG": None,
                "TEAM_ID": team["id"], "JERSEY_NUMBER": str(rng.randint(0, 55)), "POSITION": POSITIONS[slot],
                "HEIGHT": f"6-{rng.randint(1, 11)}" if slot < 11 else f"7-{rng.randint(0, 2)}",
                "WEIGHT": rng.randint(185, 270), "COLLEGE": None, "COUNTRY": "Demo",
                "DRAFT_YEAR": from_year if drafted else None, "DRAFT_ROUND": 1 if drafted else None,
                "DRAFT_NUMBER": rng.randint(1, 30) if drafted else None, "ROSTER_STATUS": 1,
                "FROM_YEAR": from_year, "TO_YEAR": 2026,
            })
            # Starters get more of the ball.
            skill[pid] = {"team": team["id"], "age": age, "from": from_year, "slot": slot,
                          "talent": max(0.15, rng.gauss(1.0 - slot * 0.065, 0.12))}
            pid += 1
    upsert(conn, "players", t.player_rows(players), ["id"])

    # ---- season totals for each player's career
    seasons = []
    for p, s in skill.items():
        peak = rng.uniform(26, 29)
        for year in range(s["from"], 2027):
            age = s["age"] - (2026 - year)
            curve = math.exp(-((age - peak) ** 2) / 40)
            gp = rng.randint(55, 80) if year < 2026 else 20
            mpg = max(8, min(37, 14 + 24 * s["talent"] * curve + rng.gauss(0, 1.5)))
            ppg = max(1.5, 25 * (s["talent"] ** 1.6) * curve + rng.gauss(0, 1.2))
            big = s["slot"] in (5, 6, 10)
            rpg = max(1, (9 if big else 4.5) * s["talent"] * curve + rng.gauss(0, 0.6))
            apg = max(0.4, (2.2 if big else 5.5) * s["talent"] * curve + rng.gauss(0, 0.5))
            fga = ppg / 1.18 / 1.45
            fta = ppg * 0.22
            fg3a = fga * (0.15 if big else 0.42)
            seasons.append({
                "player_id": p, "season": f"{year}-{str(year + 1)[-2:]}", "season_type": "Regular Season",
                "team_id": 0, "team_abbr": next(x["abbr"] for x in teams if x["id"] == s["team"]),
                "age": age, "gp": gp, "min": round(mpg * gp, 1),
                "pts": round(ppg * gp), "reb": round(rpg * gp), "oreb": round(rpg * gp * 0.25),
                "dreb": round(rpg * gp * 0.75), "ast": round(apg * gp), "stl": round(gp * rng.uniform(0.4, 1.5)),
                "blk": round(gp * (rng.uniform(0.8, 2.2) if big else rng.uniform(0.1, 0.6))),
                "tov": round(apg * gp * 0.35), "pf": round(gp * 2.1), "fgm": round(fga * gp * rng.uniform(0.43, 0.55)),
                "fga": round(fga * gp), "fg3m": round(fg3a * gp * rng.uniform(0.31, 0.41)), "fg3a": round(fg3a * gp),
                "ftm": round(fta * gp * rng.uniform(0.7, 0.9)), "fta": round(fta * gp),
                "plus_minus": round(rng.gauss(0, 120)),
                "ts_pct": round(rng.uniform(0.53, 0.64), 3), "efg_pct": round(rng.uniform(0.49, 0.6), 3),
                "usg_pct": round(min(0.36, 0.12 + 0.2 * s["talent"] * curve), 3),
                "off_rating": round(rng.uniform(108, 122), 1), "def_rating": round(rng.uniform(106, 120), 1),
                "net_rating": None, "pie": round(0.05 + 0.13 * s["talent"] * curve, 3),
                "pace": round(rng.uniform(96, 102), 2),
            })
    for r in seasons:
        r["net_rating"] = round(r["off_rating"] - r["def_rating"], 1)
    upsert(conn, "player_seasons", seasons, ["player_id", "season", "season_type", "team_id"])

    # ---- games: 20 played days before today, 14 scheduled days from today
    team_ids = [x["id"] for x in teams]
    strength = {tid: rng.gauss(0, 6) for tid in team_ids}
    games, team_games, player_games = [], [], []
    gnum = 1
    for offset in range(-40, 28, 2):
        day = today + timedelta(days=offset)
        order = team_ids[:]
        rng.shuffle(order)
        for i in range(0, 20, 2):
            home, away = order[i], order[i + 1]
            gid = f"00226{gnum:05d}"
            gnum += 1
            tip = datetime.combine(day, time(23, 30), tzinfo=timezone.utc)
            g = {"id": gid, "season": SEASON, "season_type": "Regular Season", "game_date": day, "tipoff": tip,
                 "home_team_id": home, "away_team_id": away, "home_score": None, "away_score": None,
                 "status": "scheduled", "status_detail": "7:30 pm ET"}
            if day < today:
                hs = round(rng.gauss(114 + strength[home] + 2, 10))
                as_ = round(rng.gauss(114 + strength[away], 10))
                if hs == as_:
                    hs += 1
                g.update(home_score=hs, away_score=as_, status="final", status_detail="Final")
                for tid, opp, pts, opp_pts, here in ((home, away, hs, as_, True), (away, home, as_, hs, False)):
                    abbr = next(x["abbr"] for x in teams if x["id"] == tid)
                    oabbr = next(x["abbr"] for x in teams if x["id"] == opp)
                    matchup = f"{abbr} vs. {oabbr}" if here else f"{abbr} @ {oabbr}"
                    wl = "W" if pts > opp_pts else "L"
                    team_games.append({"team_id": tid, "game_id": gid, "season": SEASON,
                                       "season_type": "Regular Season", "game_date": day, "matchup": matchup,
                                       "wl": wl, "pts": pts, "opp_pts": opp_pts, "plus_minus": pts - opp_pts})
                    roster = [p for p, s in skill.items() if s["team"] == tid]
                    weights = [skill[p]["talent"] ** 1.6 for p in roster]
                    total = sum(weights)
                    for p, w in zip(roster, weights):
                        share = w / total
                        pts_p = max(0, round(pts * share + rng.gauss(0, 3)))
                        fga = max(pts_p // 2, round(pts_p / 1.2))
                        fgm = min(fga, round(fga * rng.uniform(0.38, 0.6)))
                        fg3a = round(fga * 0.4)
                        player_games.append({
                            "player_id": p, "game_id": gid, "season": SEASON, "season_type": "Regular Season",
                            "game_date": day, "team_id": tid, "matchup": matchup, "wl": wl,
                            "min": round(max(4, min(42, 48 * share * 2.4 + rng.gauss(0, 3))), 1),
                            "pts": pts_p, "reb": max(0, round(rng.gauss(8 * share * 2, 2))),
                            "oreb": 0, "dreb": 0, "ast": max(0, round(rng.gauss(6 * share * 2, 1.5))),
                            "stl": rng.randint(0, 3), "blk": rng.randint(0, 2), "tov": rng.randint(0, 4),
                            "pf": rng.randint(0, 5), "fgm": fgm, "fga": fga,
                            "fg3m": min(fg3a, round(fg3a * rng.uniform(0.2, 0.5))), "fg3a": fg3a,
                            "ftm": max(0, pts_p - 2 * fgm) if pts_p > 2 * fgm else 0,
                            "fta": max(0, pts_p - 2 * fgm + 1) if pts_p > 2 * fgm else 0,
                            "plus_minus": round((pts - opp_pts) * share * 2 + rng.gauss(0, 4)),
                        })
            games.append(g)
    upsert(conn, "games", games, ["id"])
    upsert(conn, "team_games", team_games, ["team_id", "game_id"])
    upsert(conn, "player_games", player_games, ["player_id", "game_id"])

    # ---- standings from the results
    records: dict[int, dict] = {tid: {"w": 0, "l": 0, "pf": 0, "pa": 0, "n": 0} for tid in team_ids}
    for r in team_games:
        rec = records[r["team_id"]]
        rec["w" if r["wl"] == "W" else "l"] += 1
        rec["pf"] += r["pts"]
        rec["pa"] += r["opp_pts"]
        rec["n"] += 1
    standings = []
    for c in ("East", "West"):
        ranked = sorted((tid for tid in team_ids if conf[tid] == c),
                        key=lambda tid: (records[tid]["w"] - records[tid]["l"]), reverse=True)
        lead = records[ranked[0]]
        for rank, tid in enumerate(ranked, 1):
            rec = records[tid]
            n = max(rec["n"], 1)
            ortg = round(rec["pf"] / n / 99 * 100, 1)
            drtg = round(rec["pa"] / n / 99 * 100, 1)
            standings.append({
                "team_id": tid, "season": SEASON, "season_type": "Regular Season", "wins": rec["w"],
                "losses": rec["l"], "conf_rank": rank, "div_rank": None, "league_rank": None,
                "games_back": ((lead["w"] - rec["w"]) + (rec["l"] - lead["l"])) / 2,
                "streak": None, "last_ten": None, "home_record": None, "road_record": None,
                "pts_pg": round(rec["pf"] / n, 1), "opp_pts_pg": round(rec["pa"] / n, 1),
                "off_rating": ortg, "def_rating": drtg, "net_rating": round(ortg - drtg, 1), "pace": 99.0,
            })
    upsert(conn, "team_seasons", standings, ["team_id", "season", "season_type"])

    # ---- a few accolades for the best players
    stars = sorted(skill, key=lambda p: skill[p]["talent"], reverse=True)[:12]
    awards = []
    for i, p in enumerate(stars):
        for year in range(max(skill[p]["from"] + 3, 2019), 2026):
            season = f"{year}-{str(year + 1)[-2:]}"
            if rng.random() < 0.6:
                awards.append({"player_id": p, "award": "NBA All-Star", "season": season, "team_label": None,
                               "month": None, "week": None, "conference": None, "description": "Award",
                               "source": SOURCE})
            if rng.random() < 0.3:
                awards.append({"player_id": p, "award": "All-NBA", "season": season,
                               "team_label": str(rng.randint(1, 3)), "month": None, "week": None,
                               "conference": None, "description": "Award", "source": SOURCE})
        if i < 3:
            awards.append({"player_id": p, "award": "NBA Most Valuable Player", "season": f"202{i + 2}-2{i + 3}",
                           "team_label": None, "month": None, "week": None, "conference": None,
                           "description": "Award", "source": SOURCE})
    # Player of the Week, East and West, for each week already played.
    monday = today - timedelta(days=today.weekday() + 7)
    for week in range(3):
        day = monday - timedelta(days=7 * week)
        for c in ("East", "West"):
            pool = [p for p in stars if conf[skill[p]["team"]] == c]
            if pool:
                awards.append({"player_id": pool[week % len(pool)], "award": "NBA Player of the Week",
                               "season": SEASON, "team_label": None, "month": None, "week": day.isoformat(),
                               "conference": c, "description": "Award", "source": SOURCE})
    upsert(conn, "awards", awards, ["player_id", "award", "season", "team_label", "month", "week"])
    _retired_marks(conn, rng)
    ledger.detect(conn, SEASON, SOURCE, link_nba=False)

    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO ingest_runs (task, source, season, finished_at, ok, rows_written) VALUES (%s, %s, %s, now(), true, 0)",
            [(task, SOURCE, SEASON) for task in
             ("teams", "players", "player_stats", "gamelogs", "schedule", "standings", "awards", "scoreboard",
              "ledger")],
        )
    conn.commit()
    return {"players": len(players), "seasons": len(seasons), "games": len(games), "awards": len(awards)}
