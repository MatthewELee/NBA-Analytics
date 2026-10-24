"""Ingest tasks. Each one fetches from a source, transforms, and upserts inside a logged run."""

from __future__ import annotations

import logging
from datetime import date, timedelta

import psycopg

from . import ledger
from . import transforms as t
from .config import Settings, season_for, season_start_year, today_eastern
from .db import logged_run, upsert
from .sources import balldontlie, espn, nba

log = logging.getLogger(__name__)

GAME_SIDE_COLS = ["season", "game_date", "tipoff", "home_score", "away_score", "status", "status_detail"]


class Tasks:
    def __init__(self, conn: psycopg.Connection, settings: Settings):
        self.conn = conn
        self.settings = settings
        self._nba: nba.NbaStats | None = None
        self._espn: espn.Espn | None = None

    @property
    def nba(self) -> nba.NbaStats:
        if self._nba is None:
            self._nba = nba.NbaStats(self.settings)
        return self._nba

    @property
    def espn(self) -> espn.Espn:
        if self._espn is None:
            self._espn = espn.Espn()
        return self._espn

    # ---- lookups ---------------------------------------------------------

    def _scalar_map(self, sql: str) -> dict:
        with self.conn.cursor() as cur:
            cur.execute(sql)
            return {k: v for k, v in cur.fetchall()}

    def _known_player_ids(self) -> set[int]:
        return set(self._scalar_map("SELECT id, true FROM players"))

    # ---- teams -------------------------------------------------------------

    def teams(self) -> int:
        with logged_run(self.conn, "teams", nba.SOURCE) as run:
            try:
                branding = self.espn.teams()
                run["source"] = f"{nba.SOURCE}; {espn.SOURCE}"
            except Exception as exc:  # noqa: BLE001 - branding is optional
                log.warning("ESPN teams unavailable, keeping existing colors and logos: %s", exc)
                branding = None
            rows = t.teams_rows(nba.NbaStats.teams(), branding)
            if branding is None:
                # Don't wipe colors and ESPN ids from an earlier run.
                update = ["abbr", "city", "name", "full_name"]
            else:
                update = None
            run["rows"] = upsert(self.conn, "teams", rows, ["id"], update)
            return run["rows"]

    # ---- players -----------------------------------------------------------

    def players(self, season: str, historical: bool = False) -> int:
        with logged_run(self.conn, "players", nba.SOURCE, season) as run:
            index = self.nba.player_index(season, historical=historical)
            existing = self._scalar_map("SELECT id, slug FROM players")
            rows = t.player_rows(index, existing)
            team_ids = set(self._scalar_map("SELECT id, true FROM teams"))
            for r in rows:
                if r["team_id"] not in team_ids:
                    r["team_id"] = None
            with self.conn.cursor() as cur:
                # Anyone not in the current index is no longer on a roster.
                if not historical:
                    cur.execute("UPDATE players SET is_active = false WHERE is_active")
            run["rows"] = upsert(self.conn, "players", rows, ["id"])
            return run["rows"]

    # ---- season stats --------------------------------------------------------

    def player_stats(self, season: str, season_type: str = "Regular Season") -> int:
        with logged_run(self.conn, "player_stats", nba.SOURCE, season) as run:
            base = self.nba.player_stats(season, "Base", season_type)
            adv = self.nba.player_stats(season, "Advanced", season_type)
            rows = t.player_season_rows(base, adv, season, season_type)
            known = self._known_player_ids()
            missing = [r for r in rows if r["player_id"] not in known]
            if missing:
                log.warning("%s: skipping %d players not in the players table (run `players --historical`)",
                            season, len(missing))
            rows = [r for r in rows if r["player_id"] in known]
            run["rows"] = upsert(self.conn, "player_seasons", rows, ["player_id", "season", "season_type", "team_id"])
            return run["rows"]

    def backfill(self, first_season: str, last_season: str) -> int:
        """Loads career history: every player ever, then season totals for each season."""
        self.players(last_season, historical=True)
        self.players(last_season)  # resets is_active from the current index
        total = 0
        for year in range(season_start_year(first_season), season_start_year(last_season) + 1):
            season = f"{year}-{str(year + 1)[-2:]}"
            total += self.player_stats(season)
        return total

    # ---- games ---------------------------------------------------------------

    def gamelogs(self, season: str, season_type: str = "Regular Season") -> int:
        with logged_run(self.conn, "gamelogs", nba.SOURCE, season) as run:
            team_log = self.nba.game_log(season, "T", season_type)
            player_log = self.nba.game_log(season, "P", season_type)
            games = t.games_from_team_log(team_log, season, season_type)
            n = upsert(self.conn, "games", games, ["id"], ["home_score", "away_score", "status"])
            n += upsert(self.conn, "team_games", t.team_game_rows(team_log, season, season_type), ["team_id", "game_id"])
            known = self._known_player_ids()
            pg = [r for r in t.player_game_rows(player_log, season, season_type) if r["player_id"] in known]
            n += upsert(self.conn, "player_games", pg, ["player_id", "game_id"])
            self._merge_placeholder_games()
            run["rows"] = n
            return n

    def schedule(self, season: str) -> int:
        with logged_run(self.conn, "schedule", nba.SOURCE, season) as run:
            rows = t.games_from_schedule(self.nba.schedule(season), season)
            run["rows"] = upsert(self.conn, "games", rows, ["id"])
            self._merge_placeholder_games()
            return run["rows"]

    def standings(self, season: str) -> int:
        with logged_run(self.conn, "standings", nba.SOURCE, season) as run:
            standings = self.nba.standings(season)
            base = self.nba.team_stats(season, "Base")
            adv = self.nba.team_stats(season, "Advanced")
            self._update_conferences(t.team_conference_rows(standings))
            rows = t.team_season_rows(standings, base, adv, season)
            run["rows"] = upsert(self.conn, "team_seasons", rows, ["team_id", "season", "season_type"])
            return run["rows"]

    def _update_conferences(self, rows: list[dict]) -> None:
        with self.conn.cursor() as cur:
            cur.executemany(
                "UPDATE teams SET conference = %(conference)s, division = %(division)s, updated_at = now() WHERE id = %(id)s",
                rows,
            )

    def scoreboard(self, day: date | None = None) -> int:
        """Live and final scores for one ET day (default: yesterday and today) from ESPN."""
        days = [day] if day else [today_eastern() - timedelta(days=1), today_eastern()]
        with logged_run(self.conn, "scoreboard", espn.SOURCE, season_for(days[-1])) as run:
            teams = self._scalar_map("SELECT abbr, id FROM teams")
            n = 0
            for d in days:
                rows = t.scoreboard_rows(self.espn.scoreboard(d), teams, season_for(d))
                n += self._apply_scoreboard(rows, "espn")
            run["rows"] = n
            return n

    def bdl_games(self, start: date, end: date) -> int:
        """Fallback: scores and schedule from balldontlie when stats.nba.com is down."""
        key = self.settings.balldontlie_api_key
        if not key:
            raise RuntimeError("BALLDONTLIE_API_KEY is not set")
        with logged_run(self.conn, "scoreboard", balldontlie.SOURCE, season_for(end)) as run:
            teams = self._scalar_map("SELECT abbr, id FROM teams")
            games = balldontlie.BallDontLie(key).games(start, end)
            rows = t.bdl_game_rows(games, teams, season_for(end))
            run["rows"] = self._apply_scoreboard(rows, "bdl")
            return run["rows"]

    def _apply_scoreboard(self, rows: list[dict], prefix: str) -> int:
        """Updates the matching game (by ESPN id, else date and teams), or inserts a placeholder.

        Placeholders get ids like 'espn-401585123' and are folded into the NBA.com game
        when the schedule or game log brings it in.
        """
        n = 0
        with self.conn.cursor() as cur:
            for r in rows:
                cur.execute(
                    """SELECT id FROM games
                       WHERE (%(espn_id)s::text IS NOT NULL AND espn_id = %(espn_id)s)
                          OR (game_date = %(game_date)s AND home_team_id = %(home_team_id)s
                              AND away_team_id = %(away_team_id)s)
                       ORDER BY (id LIKE '%%-%%') LIMIT 1""",
                    r,
                )
                found = cur.fetchone()
                if found:
                    sets = ", ".join(f"{c} = %({c})s" for c in GAME_SIDE_COLS if r.get(c) is not None or c.endswith("score"))
                    if r.get("espn_id"):
                        sets += ", espn_id = %(espn_id)s"
                    cur.execute(f"UPDATE games SET {sets}, updated_at = now() WHERE id = %(id)s", {**r, "id": found[0]})
                else:
                    gid = f"espn-{r['espn_id']}" if r.get("espn_id") else \
                        f"{prefix}-{r['game_date']}-{r['home_team_id']}-{r['away_team_id']}"
                    cur.execute(
                        """INSERT INTO games (id, season, season_type, game_date, tipoff, home_team_id, away_team_id,
                                              home_score, away_score, status, status_detail, espn_id)
                           VALUES (%(id)s, %(season)s, 'Regular Season', %(game_date)s, %(tipoff)s, %(home_team_id)s,
                                   %(away_team_id)s, %(home_score)s, %(away_score)s, %(status)s, %(status_detail)s,
                                   %(espn_id)s)""",
                        {**r, "id": gid},
                    )
                n += 1
        return n

    def _merge_placeholder_games(self) -> None:
        """Folds ESPN or balldontlie placeholder games into the NBA.com game for the same matchup."""
        with self.conn.cursor() as cur:
            cur.execute(
                """WITH dup AS (
                     DELETE FROM games p USING games g
                     WHERE p.id LIKE '%-%' AND g.id NOT LIKE '%-%'
                       AND p.game_date = g.game_date AND p.home_team_id = g.home_team_id
                       AND p.away_team_id = g.away_team_id
                     RETURNING p.espn_id, p.game_date, p.home_team_id, p.away_team_id)
                   UPDATE games g SET espn_id = COALESCE(g.espn_id, dup.espn_id)
                   FROM dup
                   WHERE g.id NOT LIKE '%-%' AND g.game_date = dup.game_date
                     AND g.home_team_id = dup.home_team_id AND g.away_team_id = dup.away_team_id"""
            )

    # ---- awards and news -----------------------------------------------------

    def awards(self, limit: int | None = None) -> int:
        """Awards for every active player. One call per player, so this runs weekly."""
        with logged_run(self.conn, "awards", nba.SOURCE) as run:
            with self.conn.cursor() as cur:
                cur.execute("SELECT id FROM players WHERE is_active ORDER BY id")
                ids = [r[0] for r in cur.fetchall()][:limit]
            n = 0
            for i, pid in enumerate(ids, 1):
                rows = t.award_rows(self.nba.player_awards(pid), nba.SOURCE)
                n += upsert(self.conn, "awards", rows,
                            ["player_id", "award", "season", "team_label", "month", "week"])
                if i % 50 == 0:
                    self.conn.commit()
                    log.info("awards: %d/%d players", i, len(ids))
            run["rows"] = n
            return n

    def ledger(self, season: str) -> int:
        """Milestones, records and awards for the Ledger, computed from what's already loaded."""
        with logged_run(self.conn, "ledger", ledger.COMPUTED_SOURCE, season) as run:
            run["rows"] = ledger.detect(self.conn, season)
            return run["rows"]

    def news(self, limit: int = 50) -> int:
        with logged_run(self.conn, "news", espn.SOURCE) as run:
            teams = self._scalar_map("SELECT espn_id, id FROM teams WHERE espn_id IS NOT NULL")
            players = self._scalar_map("SELECT lower(full_name), id FROM players WHERE is_active")
            rows = t.news_rows(self.espn.news(limit), teams, players)
            run["rows"] = upsert(self.conn, "news", rows, ["id"])
            return run["rows"]
