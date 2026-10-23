"""stats.nba.com through nba_api. Every call returns plain lists of dicts.

stats.nba.com is slow, rate limited and often refuses cloud IPs, so each call
waits between requests, retries with backoff, and can go through a proxy.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable

from nba_api.stats.endpoints import (
    leaguedashplayerstats,
    leaguedashteamstats,
    leaguegamelog,
    leaguestandingsv3,
    playerawards,
    playerindex,
    scheduleleaguev2,
)
from nba_api.stats.static import teams as static_teams

from ..config import Settings
from ..util import rows

log = logging.getLogger(__name__)

SOURCE = "NBA.com (stats.nba.com via nba_api)"


class NbaStats:
    def __init__(self, settings: Settings):
        self.s = settings
        self._last_call = 0.0

    def _call(self, endpoint: Callable[..., Any], **params) -> Any:
        delay = self.s.nba_api_delay
        for attempt in range(4):
            wait = self._last_call + delay - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            try:
                result = endpoint(proxy=self.s.nba_api_proxy, timeout=self.s.nba_api_timeout, **params)
                self._last_call = time.monotonic()
                return result
            except Exception as exc:  # noqa: BLE001 - network errors vary by transport
                self._last_call = time.monotonic()
                if attempt == 3:
                    raise
                backoff = 2 ** (attempt + 1)
                log.warning("%s failed (%s), retrying in %ss", endpoint.__name__, exc, backoff)
                time.sleep(backoff)
        raise RuntimeError("unreachable")

    @staticmethod
    def _sets(result: Any) -> dict[str, list[dict]]:
        """All result sets of an endpoint response, keyed by name."""
        raw = result.get_dict()
        sets = raw.get("resultSets") or raw.get("resultSet") or []
        if isinstance(sets, dict):
            sets = [sets]
        out = {s.get("name", str(i)): rows(s) for i, s in enumerate(sets)}
        if not out:
            # Newer endpoints (scheduleleaguev2) nest their JSON; nba_api's parser flattens them.
            parsed = result.nba_response.get_data_sets(result.endpoint)
            out = {name: rows(ds) for name, ds in parsed.items()}
        return out

    # ---- Endpoints -------------------------------------------------------

    @staticmethod
    def teams() -> list[dict]:
        """The 30 franchises, bundled with nba_api (no network call)."""
        return static_teams.get_teams()

    def player_index(self, season: str, historical: bool = False) -> list[dict]:
        r = self._call(playerindex.PlayerIndex, season=season, historical_nullable="1" if historical else "")
        return self._sets(r)["PlayerIndex"]

    def player_stats(self, season: str, measure: str = "Base", season_type: str = "Regular Season") -> list[dict]:
        r = self._call(
            leaguedashplayerstats.LeagueDashPlayerStats,
            season=season,
            season_type_all_star=season_type,
            measure_type_detailed_defense=measure,
            per_mode_detailed="Totals",
        )
        return self._sets(r)["LeagueDashPlayerStats"]

    def team_stats(self, season: str, measure: str = "Base", season_type: str = "Regular Season") -> list[dict]:
        r = self._call(
            leaguedashteamstats.LeagueDashTeamStats,
            season=season,
            season_type_all_star=season_type,
            measure_type_detailed_defense=measure,
            per_mode_detailed="PerGame",
        )
        return self._sets(r)["LeagueDashTeamStats"]

    def game_log(self, season: str, who: str = "P", season_type: str = "Regular Season") -> list[dict]:
        """Every player ('P') or team ('T') box line for a season, in one call."""
        r = self._call(
            leaguegamelog.LeagueGameLog,
            season=season,
            season_type_all_star=season_type,
            player_or_team_abbreviation=who,
        )
        return self._sets(r)["LeagueGameLog"]

    def standings(self, season: str) -> list[dict]:
        r = self._call(leaguestandingsv3.LeagueStandingsV3, season=season)
        return self._sets(r)["Standings"]

    def schedule(self, season: str) -> list[dict]:
        r = self._call(scheduleleaguev2.ScheduleLeagueV2, season=season)
        return self._sets(r)["SeasonGames"]

    def player_awards(self, player_id: int) -> list[dict]:
        r = self._call(playerawards.PlayerAwards, player_id=player_id)
        return self._sets(r)["PlayerAwards"]
