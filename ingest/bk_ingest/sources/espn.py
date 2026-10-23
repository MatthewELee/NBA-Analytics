"""ESPN's public site API: scoreboard, news and team branding."""

from __future__ import annotations

from datetime import date

import requests

BASE = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
SOURCE = "ESPN"

# ESPN abbreviations that differ from NBA.com's.
ESPN_TO_NBA_ABBR = {
    "GS": "GSW",
    "NY": "NYK",
    "SA": "SAS",
    "NO": "NOP",
    "UTAH": "UTA",
    "WSH": "WAS",
}


def nba_abbr(espn_abbr: str) -> str:
    return ESPN_TO_NBA_ABBR.get(espn_abbr.upper(), espn_abbr.upper())


class Espn:
    def __init__(self, timeout: int = 20):
        self.http = requests.Session()
        self.http.headers["User-Agent"] = "BallerKnowledge/0.1 (+https://github.com/MatthewELee/NBA-Analytics)"
        self.timeout = timeout

    def _get(self, path: str, **params) -> dict:
        r = self.http.get(f"{BASE}/{path}", params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def scoreboard(self, day: date) -> dict:
        return self._get("scoreboard", dates=day.strftime("%Y%m%d"))

    def news(self, limit: int = 50) -> dict:
        return self._get("news", limit=limit)

    def teams(self) -> dict:
        return self._get("teams")
