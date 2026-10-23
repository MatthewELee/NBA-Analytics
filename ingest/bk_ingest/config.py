"""Settings from the environment, and season helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

EASTERN = ZoneInfo("America/New_York")


def season_for(day: date) -> str:
    """NBA season label for a date. Seasons start in October: 2026-10-23 -> '2026-27'."""
    start = day.year if day.month >= 10 else day.year - 1
    return f"{start}-{str(start + 1)[-2:]}"


def season_start_year(season: str) -> int:
    return int(season[:4])


def today_eastern() -> date:
    """The NBA's calendar day. A 10:30pm ET tip is still 'today' after midnight UTC."""
    return datetime.now(EASTERN).date()


def current_season() -> str:
    return season_for(today_eastern())


@dataclass(frozen=True)
class Settings:
    database_url: str
    # stats.nba.com blocks many cloud IP ranges. Route nba_api through a proxy when set.
    nba_api_proxy: str | None
    nba_api_timeout: int
    # Seconds to wait between stats.nba.com calls, to stay under its rate limit.
    nba_api_delay: float
    balldontlie_api_key: str | None

    @staticmethod
    def from_env() -> "Settings":
        url = os.environ.get("DATABASE_URL")
        if not url:
            raise SystemExit("DATABASE_URL is not set")
        return Settings(
            database_url=url,
            nba_api_proxy=os.environ.get("NBA_API_PROXY") or None,
            nba_api_timeout=int(os.environ.get("NBA_API_TIMEOUT", "45")),
            nba_api_delay=float(os.environ.get("NBA_API_DELAY", "0.8")),
            balldontlie_api_key=os.environ.get("BALLDONTLIE_API_KEY") or None,
        )
