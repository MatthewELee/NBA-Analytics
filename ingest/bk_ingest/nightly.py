"""Nightly updates from ESPN: box scores into player_games and team_games, and player matching.

NBA.com blocks GitHub's runners, so the current season is kept up to date from ESPN, which
doesn't. Career history still comes from NBA.com, loaded once from a home machine.

ESPN athletes are matched to NBA.com players by name (team and roster status break ties) and
the ESPN id is saved on the player. Anyone with no match, usually a rookie or a new signing
NBA.com hasn't been loaded for, gets a placeholder row with id = -(ESPN id). The next NBA.com
players run folds each placeholder into the real player (merge_placeholders).
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Iterable, NamedTuple

import psycopg

from .db import upsert
from .transforms import BOX_STAT_COLS, name_key
from .util import slugify

log = logging.getLogger(__name__)


class Candidate(NamedTuple):
    id: int
    team_id: int | None
    active: bool


def pick(cands: list[Candidate], team_id: int | None) -> int | None:
    """The one candidate a name points to, or None when it can't be told apart."""
    if len(cands) == 1:
        return cands[0].id
    for narrowed in ([c for c in cands if c.team_id == team_id and team_id], [c for c in cands if c.active]):
        if len(narrowed) == 1:
            return narrowed[0].id
    return None


def resolve_players(conn: psycopg.Connection, lines: list[dict], team_ids: dict[str, int],
                    season_start: int) -> dict[str, int]:
    """Maps each box score line's ESPN id to a player id, creating placeholders as needed."""
    wanted = {line["espn_id"]: line for line in lines}
    with conn.cursor() as cur:
        cur.execute("SELECT espn_id, id FROM players WHERE espn_id = ANY(%s)", (list(wanted),))
        found: dict[str, int] = dict(cur.fetchall())
        missing = [line for eid, line in wanted.items() if eid not in found]
        if not missing:
            return found

        # Only players who could be in the league now: on a roster, or played last season.
        cur.execute(
            """SELECT id, full_name, team_id, is_active FROM players
               WHERE id > 0 AND espn_id IS NULL AND (is_active OR to_year >= %s)""",
            (season_start - 1,),
        )
        by_name: dict[str, list[Candidate]] = defaultdict(list)
        for pid, name, team_id, active in cur.fetchall():
            by_name[name_key(name)].append(Candidate(pid, team_id, active))
        cur.execute("SELECT slug FROM players")
        slugs = {r[0] for r in cur.fetchall()}

        for line in missing:
            key = name_key(line["name"])
            pid = pick(by_name.get(key, []), team_ids.get(line["team_abbr"]))
            if pid is not None:
                cur.execute("UPDATE players SET espn_id = %s, updated_at = now() WHERE id = %s",
                            (line["espn_id"], pid))
                by_name[key] = [c for c in by_name[key] if c.id != pid]
            else:
                pid = -int(line["espn_id"])
                slug = slugify(line["name"]) or str(-pid)
                if slug in slugs:
                    slug = f"{slug}-{-pid}"
                slugs.add(slug)
                first, _, last = line["name"].partition(" ")
                cur.execute(
                    """INSERT INTO players (id, slug, first_name, last_name, full_name, team_id, jersey,
                                            position, is_active, headshot_url, espn_id)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, true, %s, %s)
                       ON CONFLICT (id) DO UPDATE SET espn_id = EXCLUDED.espn_id""",
                    (pid, slug, first, last or first, line["name"], team_ids.get(line["team_abbr"]),
                     line["jersey"], line["position"], line["headshot_url"], line["espn_id"]),
                )
                log.info("new player from ESPN, not yet on NBA.com: %s (%s)", line["name"], line["team_abbr"])
            found[line["espn_id"]] = pid
    return found


def store_box(conn: psycopg.Connection, game: dict, box: dict, team_ids: dict[str, int],
              player_ids: dict[str, int]) -> int:
    """Writes one game's team and player lines. `game` is the games row (id, season, ...)."""
    sides = {}
    for abbr, side in box["teams"].items():
        tid = team_ids.get(abbr)
        if tid is None:
            raise ValueError(f"unknown team {abbr!r} in ESPN game {game.get('espn_id')}")
        sides[side["home_away"]] = (abbr, tid, side["score"])
    if set(sides) != {"home", "away"}:
        raise ValueError(f"ESPN game {game.get('espn_id')} is missing a side")
    (h_abbr, h_id, h_pts), (a_abbr, a_id, a_pts) = sides["home"], sides["away"]
    common = {"game_id": game["id"], "season": game["season"], "season_type": game["season_type"],
              "game_date": game["game_date"]}

    def wl(pts, opp):
        return None if pts is None or opp is None or pts == opp else ("W" if pts > opp else "L")

    per_team = {
        h_id: {"matchup": f"{h_abbr} vs. {a_abbr}", "wl": wl(h_pts, a_pts), "pts": h_pts, "opp_pts": a_pts},
        a_id: {"matchup": f"{a_abbr} @ {h_abbr}", "wl": wl(a_pts, h_pts), "pts": a_pts, "opp_pts": h_pts},
    }
    team_rows = [
        {"team_id": tid, **common, **t,
         "plus_minus": (t["pts"] - t["opp_pts"]) if t["pts"] is not None and t["opp_pts"] is not None else None}
        for tid, t in per_team.items()
    ]
    player_rows = []
    for line in box["players"]:
        tid = team_ids.get(line["team_abbr"])
        if tid not in per_team:
            continue
        player_rows.append(
            {"player_id": player_ids[line["espn_id"]], **common, "team_id": tid,
             "matchup": per_team[tid]["matchup"], "wl": per_team[tid]["wl"],
             **{c: line[c] for c in BOX_STAT_COLS}}
        )
    n = upsert(conn, "team_games", team_rows, ["team_id", "game_id"])
    n += upsert(conn, "player_games", player_rows, ["player_id", "game_id"])
    with conn.cursor() as cur:
        # Keep the game's final score in step with the box score.
        cur.execute("UPDATE games SET home_score = %s, away_score = %s, status = 'final', updated_at = now() WHERE id = %s",
                    (h_pts, a_pts, game["id"]))
    return n


def merge_placeholders(conn: psycopg.Connection, pairs: Iterable[tuple[int, int]]) -> int:
    """Moves everything a placeholder player owns onto the real NBA.com player, then drops it."""
    n = 0
    with conn.cursor() as cur:
        for ph, real in pairs:
            cur.execute("SELECT espn_id FROM players WHERE id = %s", (ph,))
            row = cur.fetchone()
            if not row:
                continue
            cur.execute(
                """UPDATE player_games SET player_id = %(real)s WHERE player_id = %(ph)s
                     AND game_id NOT IN (SELECT game_id FROM player_games WHERE player_id = %(real)s)""",
                {"ph": ph, "real": real},
            )
            cur.execute("DELETE FROM player_games WHERE player_id = %s", (ph,))
            cur.execute("DELETE FROM player_seasons WHERE player_id = %s", (ph,))
            # Ledger keys carry the player id; drop any the real player already has, then rename.
            key = r"(^|:)%s(:|$)"
            cur.execute(
                f"""DELETE FROM ledger_items l WHERE player_id = %(ph)s AND EXISTS (
                      SELECT 1 FROM ledger_items r
                      WHERE r.dedupe_key = regexp_replace(l.dedupe_key, '{key % ph}', '\\1{real}\\2', 'g'))""",
                {"ph": ph},
            )
            cur.execute(
                f"""UPDATE ledger_items SET player_id = %(real)s,
                      dedupe_key = regexp_replace(dedupe_key, '{key % ph}', '\\1{real}\\2', 'g'),
                      source_url = COALESCE(source_url, 'https://www.nba.com/player/' || %(real)s)
                    WHERE player_id = %(ph)s""",
                {"ph": ph, "real": real},
            )
            cur.execute("UPDATE awards SET player_id = %s WHERE player_id = %s", (real, ph))
            cur.execute("UPDATE news SET player_ids = array_replace(player_ids, %s, %s) WHERE %s = ANY(player_ids)",
                        (ph, real, ph))
            cur.execute("DELETE FROM players WHERE id = %s", (ph,))
            cur.execute("UPDATE players SET espn_id = COALESCE(espn_id, %s) WHERE id = %s", (row[0], real))
            n += 1
    return n


def merge_games(conn: psycopg.Connection) -> int:
    """Folds ESPN or balldontlie placeholder games into the NBA.com game for the same matchup,
    moving their box score lines along with them."""
    with conn.cursor() as cur:
        cur.execute(
            """SELECT p.id, g.id, p.espn_id FROM games p JOIN games g
                 ON p.game_date = g.game_date AND p.home_team_id = g.home_team_id
                AND p.away_team_id = g.away_team_id
               WHERE p.id LIKE '%-%' AND g.id NOT LIKE '%-%'"""
        )
        pairs = cur.fetchall()
        for old, new, espn_id in pairs:
            for table, who in (("player_games", "player_id"), ("team_games", "team_id")):
                cur.execute(
                    f"""UPDATE {table} SET game_id = %(new)s WHERE game_id = %(old)s
                          AND {who} NOT IN (SELECT {who} FROM {table} WHERE game_id = %(new)s)""",
                    {"old": old, "new": new},
                )
                cur.execute(f"DELETE FROM {table} WHERE game_id = %s", (old,))
            cur.execute(
                """UPDATE ledger_items SET dedupe_key = replace(dedupe_key, ':' || %(old)s || ':', ':' || %(new)s || ':')
                   WHERE dedupe_key LIKE '%%:' || %(old)s || ':%%'
                     AND NOT EXISTS (SELECT 1 FROM ledger_items r
                                     WHERE r.dedupe_key = replace(ledger_items.dedupe_key, ':' || %(old)s || ':',
                                                                  ':' || %(new)s || ':'))""",
                {"old": old, "new": new},
            )
            cur.execute("DELETE FROM games WHERE id = %s", (old,))
            cur.execute("UPDATE games SET espn_id = COALESCE(espn_id, %s) WHERE id = %s", (espn_id, new))
    return len(pairs)
