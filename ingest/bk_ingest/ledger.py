"""The Ledger: milestones, records and awards, computed from what is already in the database.

Three detectors, each writing ledger_items keyed by a dedupe_key so re-runs never repeat an item:

- Career milestones: a player's running career total crosses a round number during the season.
- Records: a player passes someone on the career list for a stat, or sets the season's single-game high.
- Awards: weekly and monthly honors for the season, and season awards as they appear.

Career totals are prior regular seasons (player_seasons, team_id 0) plus this season's game logs,
so the date of each item is the date of the game that did it. Players whose earlier seasons were
never loaded are skipped, since their totals would be too low and a "milestone" could be years old.
"""

from __future__ import annotations

import logging
from datetime import date

import psycopg

from .config import season_start_year

log = logging.getLogger(__name__)

REG = "Regular Season"

# stat column -> (label used in headlines, round-number thresholds)
MILESTONES: dict[str, tuple[str, list[int]]] = {
    "pts": ("career points", [5_000, 10_000, 15_000, 20_000, 25_000, 30_000, 35_000, 40_000, 45_000]),
    "reb": ("career rebounds", [5_000, 7_500, 10_000, 12_500, 15_000, 17_500, 20_000]),
    "ast": ("career assists", [2_500, 5_000, 7_500, 10_000, 12_500, 15_000]),
    "stl": ("career steals", [1_000, 1_500, 2_000, 2_500, 3_000]),
    "blk": ("career blocks", [1_000, 1_500, 2_000, 2_500, 3_000, 3_500]),
    "fg3m": ("career 3-pointers", [1_000, 1_500, 2_000, 2_500, 3_000, 3_500, 4_000]),
    "gp": ("career games", [500, 1_000, 1_250, 1_500]),
}

# Career lists checked for "passes X": only names in the top N are worth an item.
CAREER_LIST_STATS = ["pts", "reb", "ast", "stl", "blk", "fg3m"]
CAREER_LIST_TOP = 50

# stat -> (noun, floor). A game sets the season high only if it beats every earlier game and the floor.
SEASON_HIGHS: dict[str, tuple[str, int]] = {
    "pts": ("points", 40),
    "reb": ("rebounds", 20),
    "ast": ("assists", 16),
    "fg3m": ("3-pointers", 10),
}

COMPUTED_SOURCE = "Computed from NBA.com box scores"


def detect(conn: psycopg.Connection, season: str, source: str = COMPUTED_SOURCE,
           link_nba: bool = True) -> int:
    """Writes any new ledger items for `season`. Returns how many were added."""
    n = 0
    _running_totals(conn, season)
    n += _milestones(conn, source, link_nba)
    n += _career_list(conn, season, source, link_nba)
    n += _season_highs(conn, season, source, link_nba)
    n += _awards(conn, season, link_nba)
    return n


def _running_totals(conn: psycopg.Connection, season: str) -> None:
    """Temp table: each player's career totals after each game this season."""
    cols = sorted({*MILESTONES, *CAREER_LIST_STATS} - {"gp"})
    prior = ", ".join(f"sum({c}) AS {c}" for c in cols)
    running = ", ".join(f"coalesce(p.{c}, 0) + sum(coalesce(g.{c}, 0)) OVER w AS {c}" for c in cols)
    game = ", ".join(f"coalesce(g.{c}, 0) AS game_{c}" for c in cols)
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS ledger_running")
        cur.execute(
            f"""CREATE TEMP TABLE ledger_running AS
                WITH prior AS (
                  SELECT player_id, sum(gp) AS gp, {prior}, min(left(season, 4)::int) AS first_year
                  FROM player_seasons
                  WHERE season_type = %(reg)s AND team_id = 0 AND season < %(season)s
                  GROUP BY player_id
                ),
                complete AS (
                  -- Earlier seasons are all loaded: the first one on file is the player's first season.
                  SELECT pl.id AS player_id FROM players pl LEFT JOIN prior p ON p.player_id = pl.id
                  WHERE pl.from_year IS NOT NULL
                    AND (pl.from_year >= %(start)s OR p.first_year <= pl.from_year)
                )
                SELECT g.player_id, g.game_id, g.game_date, g.team_id,
                       coalesce(p.gp, 0) + count(*) OVER w AS gp, 1 AS game_gp,
                       {running}, {game}
                FROM player_games g
                JOIN complete c ON c.player_id = g.player_id
                LEFT JOIN prior p ON p.player_id = g.player_id
                WHERE g.season = %(season)s AND g.season_type = %(reg)s AND coalesce(g.min, 0) > 0
                WINDOW w AS (PARTITION BY g.player_id ORDER BY g.game_date, g.game_id)""",
            {"reg": REG, "season": season, "start": season_start_year(season)},
        )


def _insert(conn: psycopg.Connection, rows: list[dict]) -> int:
    if not rows:
        return 0
    with conn.cursor() as cur:
        cur.executemany(
            """INSERT INTO ledger_items (kind, headline, detail, player_id, team_id, stat, value, threshold,
                                         occurred_on, source, source_url, dedupe_key)
               VALUES (%(kind)s, %(headline)s, %(detail)s, %(player_id)s, %(team_id)s, %(stat)s, %(value)s,
                       %(threshold)s, %(occurred_on)s, %(source)s, %(source_url)s, %(dedupe_key)s)
               ON CONFLICT (dedupe_key) DO NOTHING
               RETURNING id""",
            rows,
            returning=True,
        )
        added = 0
        while True:
            if cur.fetchone():
                added += 1
            if not cur.nextset():
                break
        return added


def _player_url(pid: int, link_nba: bool) -> str | None:
    return f"https://www.nba.com/player/{pid}" if link_nba else None


def _matchup(cur, game_id: str, team_id: int) -> str:
    cur.execute(
        """SELECT CASE WHEN g.home_team_id = %(t)s THEN 'against ' || a.abbr ELSE 'at ' || h.abbr END
           FROM games g JOIN teams h ON h.id = g.home_team_id JOIN teams a ON a.id = g.away_team_id
           WHERE g.id = %(g)s""",
        {"g": game_id, "t": team_id},
    )
    row = cur.fetchone()
    return row[0] if row else ""


def _milestones(conn: psycopg.Connection, source: str, link_nba: bool) -> int:
    rows = []
    with conn.cursor() as cur:
        for stat, (label, thresholds) in MILESTONES.items():
            cur.execute(
                f"""SELECT r.player_id, pl.full_name, r.team_id, r.game_id, r.game_date, r.{stat}, t
                    FROM ledger_running r
                    JOIN players pl ON pl.id = r.player_id
                    JOIN unnest(%(t)s::int[]) AS t ON r.{stat} - r.game_{stat} < t AND r.{stat} >= t""",
                {"t": thresholds},
            )
            for pid, name, team_id, game_id, day, total, threshold in cur.fetchall():
                verb = "plays in" if stat == "gp" else "passes"
                where = _matchup(conn.cursor(), game_id, team_id)
                detail = f"Career game {int(total):,}" if stat == "gp" else f"Reached {int(total):,}"
                rows.append({
                    "kind": "milestone",
                    "headline": f"{name} {verb} {threshold:,} {label}",
                    "detail": f"{detail} {where}.".replace(" .", "."),
                    "player_id": pid, "team_id": team_id, "stat": stat, "value": total, "threshold": threshold,
                    "occurred_on": day, "source": source, "source_url": _player_url(pid, link_nba),
                    "dedupe_key": f"milestone:{pid}:{stat}:{threshold}",
                })
    return _insert(conn, rows)


def _career_list(conn: psycopg.Connection, season: str, source: str, link_nba: bool) -> int:
    """'Passes X for Nth on the career list': only against players whose careers are fully loaded."""
    with conn.cursor() as cur:
        cur.execute("SELECT min(left(season, 4)::int) FROM player_seasons WHERE season_type = %s", (REG,))
        first_loaded = cur.fetchone()[0]
    # A rank is only true if every season since 1946-47 is loaded.
    with_rank = first_loaded is not None and first_loaded <= 1946
    # For the rank: everyone's career total as of the latest load, this season included.
    rows = []
    with conn.cursor() as cur:
        for stat in CAREER_LIST_STATS:
            label = MILESTONES[stat][0]
            cur.execute(
                f"""WITH career AS (
                      SELECT ps.player_id, sum(ps.{stat}) AS total
                      FROM player_seasons ps JOIN players pl ON pl.id = ps.player_id
                      WHERE ps.season_type = %(reg)s AND ps.team_id = 0
                        AND (ps.season < %(season)s OR NOT pl.is_active)
                      GROUP BY ps.player_id
                    ),
                    board AS (
                      SELECT c.player_id, c.total, pl.full_name
                      FROM career c JOIN players pl ON pl.id = c.player_id
                      WHERE NOT pl.is_active AND c.total > 0
                      ORDER BY c.total DESC LIMIT %(top)s
                    ),
                    alltime AS (
                      SELECT player_id, sum({stat}) AS total FROM player_seasons
                      WHERE season_type = %(reg)s AND team_id = 0 GROUP BY player_id
                    )
                    SELECT r.player_id, pl.full_name, r.team_id, r.game_id, r.game_date, r.{stat},
                           b.player_id, b.full_name, b.total,
                           1 + (SELECT count(*) FROM alltime a
                                WHERE a.player_id <> r.player_id AND a.total > r.{stat}) AS rk
                    FROM ledger_running r
                    JOIN players pl ON pl.id = r.player_id
                    JOIN board b ON b.player_id <> r.player_id
                                AND r.{stat} - r.game_{stat} <= b.total AND r.{stat} > b.total""",
                {"reg": REG, "season": season, "top": CAREER_LIST_TOP},
            )
            # One item per game: name the highest total passed, and mention the rest.
            games: dict[tuple, list] = {}
            for row in cur.fetchall():
                games.setdefault((row[0], row[3]), []).append(row)
            for passed in games.values():
                passed.sort(key=lambda r: r[8], reverse=True)
                pid, name, team_id, game_id, day, total, passed_id, passed_name, passed_total, rk = passed[0]
                where = _matchup(conn.cursor(), game_id, team_id)
                place = f" for {_ordinal(int(rk))} all time" if with_rank else ""
                others = [r[7] for r in passed[1:]]
                also = f" Also passes {_join(others)}." if others else ""
                rows.append({
                    "kind": "record",
                    "headline": f"{name} passes {passed_name} in {label}{place}",
                    "detail": f"{int(total):,} after the game {where}; {passed_name} finished with "
                              f"{int(passed_total):,}.{also}",
                    "player_id": pid, "team_id": team_id, "stat": stat, "value": total,
                    "threshold": passed_total, "occurred_on": day, "source": source,
                    "source_url": _player_url(pid, link_nba),
                    "dedupe_key": f"passes:{pid}:{stat}:{passed_id}",
                })
    return _insert(conn, rows)


def _season_highs(conn: psycopg.Connection, season: str, source: str, link_nba: bool) -> int:
    rows = []
    with conn.cursor() as cur:
        for stat, (noun, floor) in SEASON_HIGHS.items():
            cur.execute(
                f"""WITH g AS (
                      SELECT pg.player_id, pg.team_id, pg.game_id, pg.game_date, pg.matchup, pg.{stat} AS v,
                             max(pg.{stat}) OVER (ORDER BY pg.game_date
                                                  RANGE BETWEEN UNBOUNDED PRECEDING AND '1 day' PRECEDING) AS before
                      FROM player_games pg
                      WHERE pg.season = %(season)s AND pg.season_type = %(reg)s AND pg.{stat} IS NOT NULL
                    )
                    SELECT g.player_id, pl.full_name, g.team_id, g.game_id, g.game_date, g.matchup, g.v, g.before
                    FROM g JOIN players pl ON pl.id = g.player_id
                    WHERE g.v >= %(floor)s AND g.v > coalesce(g.before, 0)""",
                {"season": season, "reg": REG, "floor": floor},
            )
            for pid, name, team_id, game_id, day, matchup, v, before in cur.fetchall():
                prev = f" The previous high was {before}." if before else ""
                verb = "scores" if stat == "pts" else ("makes" if stat == "fg3m" else "has")
                rows.append({
                    "kind": "record",
                    "headline": f"{name} {verb} {v} {noun}, the season high",
                    "detail": f"{_where(matchup)}, {season.replace('-', '–')} regular season.{prev}".lstrip(", "),
                    "player_id": pid, "team_id": team_id, "stat": stat, "value": v, "threshold": before,
                    "occurred_on": day, "source": source, "source_url": _player_url(pid, link_nba),
                    "dedupe_key": f"season-high:{season}:{stat}:{game_id}:{pid}",
                })
    return _insert(conn, rows)


# Season awards worth an item. Weekly and monthly honors are always included.
SEASON_AWARDS = {
    "NBA Most Valuable Player": "is named MVP",
    "NBA Rookie of the Year": "is named Rookie of the Year",
    "NBA Defensive Player of the Year": "is named Defensive Player of the Year",
    "NBA Sixth Man of the Year": "is named Sixth Man of the Year",
    "NBA Most Improved Player": "is named Most Improved Player",
    "NBA Clutch Player of the Year": "is named Clutch Player of the Year",
    "NBA Finals Most Valuable Player": "is named Finals MVP",
    "All-NBA": "makes All-NBA",
    "All-Defensive Team": "makes All-Defensive",
    "NBA All-Star": "is named an All-Star",
}


def _awards(conn: psycopg.Connection, season: str, link_nba: bool) -> int:
    """This season's awards. Season awards are announced before the label rolls over in October.

    Weekly and monthly awards carry their own date. Season awards don't, so they're dated the
    day this job first sees them, which is within a week of the announcement.
    """
    with conn.cursor() as cur:
        cur.execute(
            """SELECT a.id, a.player_id, pl.full_name, pl.team_id, a.award, a.season, a.team_label, a.month, a.week,
                      a.conference, a.source
               FROM awards a JOIN players pl ON pl.id = a.player_id
               WHERE a.season = %s""",
            (season,),
        )
        found = cur.fetchall()
        cur.execute("SELECT current_date")
        today = cur.fetchone()[0]
    rows = []
    for _, pid, name, team_id, award, aseason, team_label, month, week, conf, source in found:
        dated = week or month
        if not dated and award not in SEASON_AWARDS:
            continue
        label = aseason.replace("-", "–")
        if dated:
            what = award.removeprefix("NBA ").strip()
            conf_label = f"{conf}ern Conference " if conf in ("East", "West") else ""
            headline = f"{name} is named {conf_label}{what}"
            d = date.fromisoformat(dated)
            detail = (f"Week of {d:%b} {d.day}, {label}." if week else f"{d:%B %Y}, {label}.")
        else:
            suffix = {"1": " First Team", "2": " Second Team", "3": " Third Team"}.get(team_label or "", "")
            headline = f"{name} {SEASON_AWARDS[award]}{suffix}"
            detail = f"{label} season."
        rows.append({
            "kind": "award", "headline": headline, "detail": detail, "player_id": pid,
            "team_id": team_id,
            "stat": None, "value": None, "threshold": None, "occurred_on": dated or today,
            "source": source, "source_url": _player_url(pid, link_nba),
            "dedupe_key": f"award:{pid}:{award}:{aseason}:{team_label or ''}:{month or ''}:{week or ''}",
        })
    return _insert(conn, rows)


def _where(matchup: str | None) -> str:
    """'GSW vs. LAL' -> 'Against LAL', 'GSW @ LAL' -> 'At LAL'."""
    parts = (matchup or "").split()
    if len(parts) != 3:
        return ""
    return f"{'At' if parts[1] == '@' else 'Against'} {parts[2]}"


def _join(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def _ordinal(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"
