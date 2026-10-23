"""balldontlie.io, the fallback for games and scores when stats.nba.com is unreachable.

The free tier covers teams, players and games, which is what the fallback uses.
It needs an API key (BALLDONTLIE_API_KEY).
"""

from __future__ import annotations

from datetime import date

import requests

BASE = "https://api.balldontlie.io/v1"
SOURCE = "balldontlie"


class BallDontLie:
    def __init__(self, api_key: str, timeout: int = 20):
        self.http = requests.Session()
        self.http.headers["Authorization"] = api_key
        self.timeout = timeout

    def games(self, start: date, end: date) -> list[dict]:
        out: list[dict] = []
        cursor = None
        while True:
            params: dict = {"start_date": start.isoformat(), "end_date": end.isoformat(), "per_page": 100}
            if cursor:
                params["cursor"] = cursor
            r = self.http.get(f"{BASE}/games", params=params, timeout=self.timeout)
            r.raise_for_status()
            body = r.json()
            out.extend(body.get("data", []))
            cursor = (body.get("meta") or {}).get("next_cursor")
            if not cursor:
                return out
