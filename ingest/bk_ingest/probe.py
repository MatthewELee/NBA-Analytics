"""Checks which data sources answer from wherever this runs (a GitHub runner, your laptop)."""

from __future__ import annotations

import time

import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/126.0 Safari/537.36",
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com",
    "Accept": "application/json, text/plain, */*",
}

TARGETS = [
    ("NBA CDN schedule", "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json"),
    ("NBA CDN scoreboard", "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json"),
    ("ESPN scoreboard", "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"),
    ("stats.nba.com", "https://stats.nba.com/stats/commonteamyears?LeagueID=00"),
]


def run(timeout: int = 20) -> list[tuple[str, str]]:
    out = []
    for name, url in TARGETS:
        start = time.monotonic()
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            result = f"HTTP {r.status_code}, {len(r.content):,} bytes"
        except Exception as exc:  # noqa: BLE001 - report whatever the network does
            result = f"{type(exc).__name__}"
        out.append((name, f"{result} in {time.monotonic() - start:.1f}s"))
    return out

