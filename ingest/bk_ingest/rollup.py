"""Season totals and standings for one season, computed from the game tables.

Used for the current season, which is kept up to date from ESPN box scores. Writes the columns
box scores can support: totals, TS%, eFG% and usage for players; record, ranks, games back,
streaks, splits, ratings and pace for teams. Columns only NBA.com has (PIE, player ratings)
are left as they are.

Ranks are by win percentage, then wins. They ignore the NBA's tiebreakers, so two teams with the
same record can be listed in either order until NBA.com standings are loaded.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date

import psycopg

from .config import season_start_year
from .db import upsert
from .transforms import TEAM_GROUPS

PLAYER_TOTALS = ["min", "pts", "reb", "oreb", "dreb", "ast", "stl", "blk", "tov", "pf",
                 "fgm", "fga", "fg3m", "fg3a", "ftm", "fta", "plus_minus"]


def player_seasons(conn: psycopg.Connection, season: str) -> int:
    sums = ", ".join(f"sum(g.{c}) AS {c}" for c in PLAYER_TOTALS)
    cols = ", ".join(PLAYER_TOTALS)
    updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in
                        ["team_abbr", "age", "gp", *PLAYER_TOTALS, "ts_pct", "efg_pct", "usg_pct"])
    # Age as the NBA counts it: on February 1 of the season.
    age_on = date(season_start_year(season) + 1, 2, 1)
    with conn.cursor() as cur:
        cur.execute(
            f"""WITH team_game AS (
                  SELECT game_id, team_id, sum(min) AS min,
                         sum(coalesce(fga, 0) + 0.44 * coalesce(fta, 0) + coalesce(tov, 0)) AS used
                  FROM player_games WHERE season = %(season)s GROUP BY game_id, team_id
                ),
                agg AS (
                  SELECT g.player_id, g.season_type, count(*) AS gp, {sums},
                         sum(coalesce(g.fga, 0) + 0.44 * coalesce(g.fta, 0) + coalesce(g.tov, 0)) AS used,
                         sum(g.min * t.used / NULLIF(t.min / 5.0, 0)) AS team_used,
                         (array_agg(g.team_id ORDER BY g.game_date DESC))[1] AS last_team
                  FROM player_games g JOIN team_game t USING (game_id, team_id)
                  WHERE g.season = %(season)s
                  GROUP BY g.player_id, g.season_type
                )
                INSERT INTO player_seasons (player_id, season, season_type, team_id, team_abbr, age, gp, {cols},
                                            ts_pct, efg_pct, usg_pct)
                SELECT a.player_id, %(season)s, a.season_type, 0, tm.abbr,
                       date_part('year', age(%(age_on)s::date, p.birthdate))::numeric,
                       a.gp, {", ".join(f"a.{c}" for c in PLAYER_TOTALS)},
                       round(a.pts / NULLIF(2 * (a.fga + 0.44 * a.fta), 0), 3),
                       round((a.fgm + 0.5 * a.fg3m) / NULLIF(a.fga, 0)::numeric, 3),
                       round(a.used / NULLIF(a.team_used, 0), 3)
                FROM agg a JOIN players p ON p.id = a.player_id LEFT JOIN teams tm ON tm.id = a.last_team
                ON CONFLICT (player_id, season, season_type, team_id) DO UPDATE SET {updates}, updated_at = now()""",
            {"season": season, "age_on": age_on},
        )
        n = cur.rowcount
        # Rosters follow the box scores: a player's team is the last one they played for.
        cur.execute(
            """UPDATE players p SET team_id = last.team_id, is_active = true, updated_at = now()
               FROM (SELECT DISTINCT ON (player_id) player_id, team_id FROM player_games
                     WHERE season = %(season)s ORDER BY player_id, game_date DESC) last
               WHERE p.id = last.player_id AND (p.team_id IS DISTINCT FROM last.team_id OR NOT p.is_active)""",
            {"season": season},
        )
    return n


def team_seasons(conn: psycopg.Connection, season: str) -> int:
    fill_team_groups(conn)
    with conn.cursor() as cur:
        cur.execute(
            """WITH poss AS (
                 SELECT game_id, team_id, sum(min) AS min,
                        sum(coalesce(fga, 0) - coalesce(oreb, 0) + coalesce(tov, 0) + 0.44 * coalesce(fta, 0)) AS poss
                 FROM player_games WHERE season = %(season)s GROUP BY game_id, team_id
               )
               SELECT t.team_id, t.season_type, t.wl, t.pts, t.opp_pts, g.home_team_id = t.team_id AS home,
                      (p.poss + o.poss) / 2 AS poss, p.min,
                      tm.conference, tm.division
               FROM team_games t
               JOIN games g ON g.id = t.game_id
               JOIN teams tm ON tm.id = t.team_id
               LEFT JOIN poss p ON p.game_id = t.game_id AND p.team_id = t.team_id
               LEFT JOIN poss o ON o.game_id = t.game_id AND o.team_id <> t.team_id
               WHERE t.season = %(season)s AND t.wl IS NOT NULL
               ORDER BY t.team_id, t.game_date, g.tipoff NULLS LAST""",
            {"season": season},
        )
        games = cur.fetchall()

    teams: dict[tuple[str, int], dict] = {}
    for team_id, stype, wl, pts, opp, home, poss, mins, conf, div in games:
        s = teams.setdefault((stype, team_id), {
            "team_id": team_id, "season_type": stype, "conference": conf, "division": div,
            "results": [], "home": [0, 0], "road": [0, 0], "pts": 0, "opp": 0,
            "rated_pts": 0, "rated_opp": 0, "poss": 0.0, "min": 0.0,
        })
        s["results"].append(wl)
        split = s["home" if home else "road"]
        split[0 if wl == "W" else 1] += 1
        s["pts"] += pts or 0
        s["opp"] += opp or 0
        if poss and mins:
            s["rated_pts"] += pts or 0
            s["rated_opp"] += opp or 0
            s["poss"] += float(poss)
            s["min"] += float(mins)

    rows = []
    for (stype, _), s in teams.items():
        res = s["results"]
        w, gp = res.count("W"), len(res)
        streak_len = len(res) - len(list(_strip_tail(res)))
        poss = s["poss"]
        ortg = round(100 * s["rated_pts"] / poss, 1) if poss else None
        drtg = round(100 * s["rated_opp"] / poss, 1) if poss else None
        last_ten = res[-10:]
        rows.append({
            "team_id": s["team_id"], "season": season, "season_type": stype,
            "wins": w, "losses": gp - w,
            "streak": f"{res[-1]} {streak_len}",
            "last_ten": f"{last_ten.count('W')}-{len(last_ten) - last_ten.count('W')}",
            "home_record": "-".join(map(str, s["home"])), "road_record": "-".join(map(str, s["road"])),
            "pts_pg": round(s["pts"] / gp, 1), "opp_pts_pg": round(s["opp"] / gp, 1),
            "off_rating": ortg, "def_rating": drtg,
            "net_rating": round(ortg - drtg, 1) if ortg is not None and drtg is not None else None,
            # Possessions per 48 minutes; team minutes are five players' worth.
            "pace": round(48 * poss / (s["min"] / 5), 2) if s["min"] else None,
            "_conf": s["conference"], "_div": s["division"],
        })
    _rank(rows)
    for r in rows:
        del r["_conf"], r["_div"]
    return upsert(conn, "team_seasons", rows, ["team_id", "season", "season_type"])


def _strip_tail(results: list[str]):
    """Results with the current streak removed."""
    end = len(results)
    while end and results[end - 1] == results[-1]:
        end -= 1
    return results[:end]


def _rank(rows: list[dict]) -> None:
    def pct(r):
        gp = r["wins"] + r["losses"]
        return (r["wins"] / gp if gp else 0, r["wins"])

    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        groups[("league", r["season_type"])].append(r)
        groups[("conf", r["season_type"], r["_conf"])].append(r)
        groups[("div", r["season_type"], r["_div"])].append(r)
    for key, members in groups.items():
        members.sort(key=pct, reverse=True)
        col = {"league": "league_rank", "conf": "conf_rank", "div": "div_rank"}[key[0]]
        known = key[0] == "league" or key[-1] is not None
        for i, r in enumerate(members, 1):
            r[col] = i if known else None
        if key[0] == "conf" and known:
            top = members[0]
            for r in members:
                r["games_back"] = ((top["wins"] - r["wins"]) + (r["losses"] - top["losses"])) / 2
    for r in rows:
        r.setdefault("conf_rank", None)
        r.setdefault("div_rank", None)
        r.setdefault("games_back", None)


def fill_team_groups(conn: psycopg.Connection) -> None:
    """Sets conference and division for teams that never got them from NBA.com standings."""
    with conn.cursor() as cur:
        cur.executemany(
            "UPDATE teams SET conference = %s, division = %s WHERE abbr = %s AND conference IS NULL",
            [(conf, div, abbr) for abbr, (conf, div) in TEAM_GROUPS.items()],
        )
