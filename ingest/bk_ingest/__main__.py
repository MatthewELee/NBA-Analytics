"""Command line: python -m bk_ingest <command> [options]. Run from the ingest/ folder."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, timedelta

from .config import Settings, current_season, today_eastern
from .db import connect, migrate
from .tasks import Tasks

log = logging.getLogger("bk_ingest")

# Groups the scheduler runs. Each step runs even if an earlier one failed.
GROUPS = {
    "daily": ["teams", "players", "standings", "player-stats", "gamelogs", "schedule"],
    "live": ["scoreboard"],
    "hourly": ["news", "scoreboard"],
    "weekly": ["awards"],
}


def run_step(tasks: Tasks, step: str, args) -> None:
    season = args.season
    if step == "teams":
        tasks.teams()
    elif step == "players":
        tasks.players(season, historical=args.historical)
    elif step == "player-stats":
        tasks.player_stats(season, args.season_type)
    elif step == "gamelogs":
        tasks.gamelogs(season, args.season_type)
    elif step == "schedule":
        tasks.schedule(season)
    elif step == "standings":
        tasks.standings(season)
    elif step == "scoreboard":
        tasks.scoreboard(date.fromisoformat(args.date) if args.date else None)
    elif step == "news":
        tasks.news()
    elif step == "awards":
        tasks.awards(args.limit)
    elif step == "backfill":
        tasks.backfill(args.first_season, season)
    elif step == "bdl-games":
        today = today_eastern()
        tasks.bdl_games(today - timedelta(days=3), today + timedelta(days=7))
    else:
        raise SystemExit(f"unknown command: {step}")


def main(argv: list[str] | None = None) -> int:
    commands = sorted({*GROUPS, "migrate", "backfill", "bdl-games", "demo", *(s for g in GROUPS.values() for s in g)})
    p = argparse.ArgumentParser(prog="bk_ingest", description="Load NBA data into the Baller Knowledge database.")
    p.add_argument("command", choices=commands)
    p.add_argument("--season", default=current_season(), help="NBA season label, e.g. 2026-27 (default: current)")
    p.add_argument("--season-type", default="Regular Season", choices=["Regular Season", "Playoffs", "PlayIn"])
    p.add_argument("--historical", action="store_true", help="players: include every player ever")
    p.add_argument("--first-season", default="1996-97", help="backfill: first season to load")
    p.add_argument("--date", help="scoreboard: ET date, YYYY-MM-DD")
    p.add_argument("--limit", type=int, help="awards: only the first N active players")
    p.add_argument("--confirm-demo", action="store_true",
                   help="demo: required, since demo data is fictional and must not reach production")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = Settings.from_env()
    conn = connect(settings.database_url)

    if args.command == "migrate":
        applied = migrate(conn)
        log.info("applied %s", applied or "nothing (up to date)")
        return 0

    if args.command == "demo":
        if not args.confirm_demo:
            raise SystemExit("demo writes fictional players and games. Re-run with --confirm-demo on a dev database.")
        from .demo import seed

        log.info("seeded demo data: %s", seed(conn, today_eastern()))
        return 0

    tasks = Tasks(conn, settings)
    steps = GROUPS.get(args.command, [args.command])
    failed: list[str] = []
    for step in steps:
        try:
            log.info("running %s (%s)", step, args.season)
            run_step(tasks, step, args)
        except Exception:  # noqa: BLE001 - keep going, report at the end
            log.exception("%s failed", step)
            failed.append(step)

    nba_steps = {"players", "standings", "player-stats", "gamelogs", "schedule"}
    if args.command == "daily" and nba_steps & set(failed) and settings.balldontlie_api_key:
        log.warning("stats.nba.com steps failed; falling back to balldontlie for recent and upcoming games")
        try:
            run_step(tasks, "bdl-games", args)
        except Exception:  # noqa: BLE001
            log.exception("balldontlie fallback failed")
            failed.append("bdl-games")

    if failed:
        log.error("failed: %s", ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
