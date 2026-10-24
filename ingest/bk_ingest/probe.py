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


def espn_sample(timeout: int = 20) -> list[str]:
    """Prints the shape of one finished game's ESPN box score, so the parser can be checked."""
    import json
    from datetime import date, timedelta

    base = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
    lines = []
    for back in range(1, 6):
        day = (date.today() - timedelta(days=back)).strftime("%Y%m%d")
        sb = requests.get(f"{base}/scoreboard", params={"dates": day}, timeout=timeout).json()
        done = [e for e in sb.get("events", []) if e["status"]["type"].get("completed")]
        if done:
            break
    else:
        return ["no finished games in the last 5 days"]
    ev = done[0]
    comp = ev["competitions"][0]
    lines.append(f"event {ev['id']} {ev['date']} season={json.dumps(ev.get('season'))}")
    lines.append(f"competitors: {[(c['homeAway'], c['team']['abbreviation'], c['team']['id'], c.get('score')) for c in comp['competitors']]}")
    lines.append(f"status: {json.dumps(ev['status'])[:400]}")
    s = requests.get(f"{base}/summary", params={"event": ev["id"]}, timeout=timeout).json()
    lines.append(f"summary keys: {sorted(s)}")
    box = s.get("boxscore", {})
    lines.append(f"boxscore keys: {sorted(box)}")
    for t in box.get("teams", [])[:1]:
        lines.append(f"team block keys: {sorted(t)}; team={t['team'].get('abbreviation')}")
        lines.append(f"team stats: {json.dumps(t.get('statistics'))[:2500]}")
    for p in box.get("players", [])[:1]:
        lines.append(f"players block keys: {sorted(p)}; team={p['team'].get('abbreviation')}")
        st = p["statistics"][0]
        lines.append(f"stat block keys: {sorted(st)}")
        lines.append(f"names={st.get('names')} keys={st.get('keys')} labels={st.get('labels')}")
        lines.append(f"totals={st.get('totals')}")
        for a in st.get("athletes", [])[:2]:
            lines.append(f"athlete: {json.dumps(a)[:1500]}")
        dnp = [a for a in st.get("athletes", []) if a.get("didNotPlay")]
        if dnp:
            lines.append(f"dnp athlete: {json.dumps(dnp[0])[:800]}")
    hdr = s.get("header", {})
    lines.append(f"header season={json.dumps(hdr.get('season'))} competitions[0] keys={sorted(hdr.get('competitions', [{}])[0])}")
    return lines
