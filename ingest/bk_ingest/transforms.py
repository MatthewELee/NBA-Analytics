"""Pure functions that turn source payloads into table rows. No network, no database."""

from __future__ import annotations

import hashlib
from typing import Iterable

from .config import EASTERN
from .sources.espn import nba_abbr
from .util import slugify, to_date, to_datetime, to_float, to_int

HEADSHOT = "https://cdn.nba.com/headshots/nba/latest/1040x760/{id}.png"
TEAM_LOGO = "https://cdn.nba.com/logos/nba/{id}/global/L/logo.svg"

SEASON_TYPE_BY_GAME_PREFIX = {
    "001": "Pre Season",
    "002": "Regular Season",
    "003": "All Star",
    "004": "Playoffs",
    "005": "PlayIn",
    "006": "NBA Cup",
}


def season_type_for_game(game_id: str) -> str:
    return SEASON_TYPE_BY_GAME_PREFIX.get(str(game_id)[:3], "Regular Season")


# ---- Teams -----------------------------------------------------------------


def teams_rows(static: list[dict], espn_teams: dict | None = None) -> list[dict]:
    """Franchises from nba_api's bundled list, with colors and ESPN ids when ESPN answered."""
    branding: dict[str, dict] = {}
    if espn_teams:
        for league in espn_teams.get("sports", [{}])[0].get("leagues", []):
            for entry in league.get("teams", []):
                t = entry.get("team", entry)
                logos = t.get("logos") or []
                branding[nba_abbr(t.get("abbreviation", ""))] = {
                    "espn_id": str(t.get("id")) if t.get("id") else None,
                    "color_primary": (t.get("color") or None),
                    "color_secondary": (t.get("alternateColor") or None),
                    "logo_url": logos[0].get("href") if logos else None,
                }
    out = []
    for t in static:
        b = branding.get(t["abbreviation"], {})
        out.append(
            {
                "id": t["id"],
                "abbr": t["abbreviation"],
                "city": t["city"],
                "name": t["nickname"],
                "full_name": t["full_name"],
                "espn_id": b.get("espn_id"),
                "color_primary": b.get("color_primary"),
                "color_secondary": b.get("color_secondary"),
                "logo_url": b.get("logo_url") or TEAM_LOGO.format(id=t["id"]),
            }
        )
    return out


# ---- Players ---------------------------------------------------------------


def player_rows(index: list[dict], existing_slugs: dict[int, str] | None = None) -> list[dict]:
    """Players from PlayerIndex. Slugs stay stable once assigned; clashes get the id appended."""
    existing_slugs = existing_slugs or {}
    taken = {slug: pid for pid, slug in existing_slugs.items()}
    out = []
    for p in index:
        pid = to_int(p.get("PERSON_ID"))
        if pid is None:
            continue
        first = (p.get("PLAYER_FIRST_NAME") or "").strip()
        last = (p.get("PLAYER_LAST_NAME") or "").strip()
        full = f"{first} {last}".strip()
        slug = existing_slugs.get(pid)
        if not slug:
            slug = p.get("PLAYER_SLUG") or slugify(full) or str(pid)
            if taken.get(slug, pid) != pid:
                slug = f"{slug}-{pid}"
            taken[slug] = pid
        team_id = to_int(p.get("TEAM_ID")) or None
        draft_year = to_int(p.get("DRAFT_YEAR"))
        out.append(
            {
                "id": pid,
                "slug": slug,
                "first_name": first,
                "last_name": last,
                "full_name": full,
                "team_id": team_id,
                "jersey": (str(p["JERSEY_NUMBER"]) if p.get("JERSEY_NUMBER") not in (None, "") else None),
                "position": p.get("POSITION") or None,
                "height": p.get("HEIGHT") or None,
                "weight_lb": to_int(p.get("WEIGHT")),
                "country": p.get("COUNTRY") or None,
                "college": p.get("COLLEGE") or None,
                "draft_year": draft_year,
                "draft_round": to_int(p.get("DRAFT_ROUND")) if draft_year else None,
                "draft_number": to_int(p.get("DRAFT_NUMBER")) if draft_year else None,
                "from_year": to_int(p.get("FROM_YEAR")),
                "to_year": to_int(p.get("TO_YEAR")),
                "is_active": to_int(p.get("ROSTER_STATUS")) == 1,
                "headshot_url": HEADSHOT.format(id=pid),
            }
        )
    return out


# ---- Player seasons --------------------------------------------------------

_TOTAL_COLS = {
    "gp": "GP", "min": "MIN", "pts": "PTS", "reb": "REB", "oreb": "OREB", "dreb": "DREB",
    "ast": "AST", "stl": "STL", "blk": "BLK", "tov": "TOV", "pf": "PF", "fgm": "FGM",
    "fga": "FGA", "fg3m": "FG3M", "fg3a": "FG3A", "ftm": "FTM", "fta": "FTA",
    "plus_minus": "PLUS_MINUS",
}
_ADV_COLS = {
    "ts_pct": "TS_PCT", "efg_pct": "EFG_PCT", "usg_pct": "USG_PCT", "off_rating": "OFF_RATING",
    "def_rating": "DEF_RATING", "net_rating": "NET_RATING", "pie": "PIE", "pace": "PACE",
}


def player_season_rows(base: list[dict], advanced: list[dict], season: str, season_type: str) -> list[dict]:
    """Season totals (base, PerMode=Totals) merged with advanced rates, one row per player."""
    adv = {to_int(r.get("PLAYER_ID")): r for r in advanced}
    out = []
    for r in base:
        pid = to_int(r.get("PLAYER_ID"))
        if pid is None:
            continue
        row = {
            "player_id": pid,
            "season": season,
            "season_type": season_type,
            "team_id": 0,
            "team_abbr": r.get("TEAM_ABBREVIATION") or None,
            "age": to_float(r.get("AGE")),
        }
        for col, src in _TOTAL_COLS.items():
            row[col] = to_float(r.get(src)) if col == "min" else to_int(r.get(src))
        row["gp"] = row["gp"] or 0
        a = adv.get(pid, {})
        for col, src in _ADV_COLS.items():
            row[col] = to_float(a.get(src))
        out.append(row)
    return out


# ---- Game logs -------------------------------------------------------------


def player_game_rows(log: list[dict], season: str, season_type: str) -> list[dict]:
    out = []
    for r in log:
        out.append(
            {
                "player_id": to_int(r["PLAYER_ID"]),
                "game_id": str(r["GAME_ID"]),
                "season": season,
                "season_type": season_type,
                "game_date": to_date(r["GAME_DATE"]),
                "team_id": to_int(r["TEAM_ID"]),
                "matchup": r.get("MATCHUP") or "",
                "wl": r.get("WL") or None,
                **{col: (to_float(r.get(src)) if col == "min" else to_int(r.get(src)))
                   for col, src in _TOTAL_COLS.items() if col != "gp"},
            }
        )
    return out


def team_game_rows(log: list[dict], season: str, season_type: str) -> list[dict]:
    out = []
    for r in log:
        pts = to_int(r.get("PTS"))
        pm = to_int(r.get("PLUS_MINUS"))
        out.append(
            {
                "team_id": to_int(r["TEAM_ID"]),
                "game_id": str(r["GAME_ID"]),
                "season": season,
                "season_type": season_type,
                "game_date": to_date(r["GAME_DATE"]),
                "matchup": r.get("MATCHUP") or "",
                "wl": r.get("WL") or None,
                "pts": pts,
                "opp_pts": (pts - pm) if pts is not None and pm is not None else None,
                "plus_minus": pm,
            }
        )
    return out


def games_from_team_log(log: list[dict], season: str, season_type: str) -> list[dict]:
    """Final games, built by pairing the two team lines of each game. 'vs.' marks the home side."""
    by_game: dict[str, dict] = {}
    for r in log:
        gid = str(r["GAME_ID"])
        g = by_game.setdefault(gid, {"id": gid, "season": season, "season_type": season_type,
                                     "game_date": to_date(r["GAME_DATE"]), "status": "final"})
        side = "home" if " vs. " in (r.get("MATCHUP") or "") else "away"
        g[f"{side}_team_id"] = to_int(r["TEAM_ID"])
        g[f"{side}_score"] = to_int(r.get("PTS"))
    return [g for g in by_game.values() if "home_team_id" in g and "away_team_id" in g]


def games_from_schedule(schedule: list[dict], season: str) -> list[dict]:
    status_by_code = {1: "scheduled", 2: "live", 3: "final"}
    out = []
    for r in schedule:
        gid = str(r.get("gameId") or "")
        home, away = to_int(r.get("homeTeam_teamId")), to_int(r.get("awayTeam_teamId"))
        if not gid or not home or not away:
            continue  # TBD playoff and Cup slots
        status = status_by_code.get(to_int(r.get("gameStatus")) or 1, "scheduled")
        if "PPD" in str(r.get("gameStatusText", "")).upper() or to_int(r.get("postponedStatus")) not in (None, 0):
            status = "postponed"
        out.append(
            {
                "id": gid,
                "season": season,
                "season_type": season_type_for_game(gid),
                "game_date": to_date(r.get("gameDateEst") or r.get("gameDate")),
                "tipoff": to_datetime(r.get("gameDateTimeUTC")),
                "home_team_id": home,
                "away_team_id": away,
                "home_score": to_int(r.get("homeTeam_score")) if status != "scheduled" else None,
                "away_score": to_int(r.get("awayTeam_score")) if status != "scheduled" else None,
                "status": status,
                "status_detail": (r.get("gameStatusText") or "").strip() or None,
            }
        )
    return out


# ---- Standings and team ratings --------------------------------------------


def team_season_rows(standings: list[dict], base: list[dict], advanced: list[dict],
                     season: str, season_type: str = "Regular Season") -> list[dict]:
    adv = {to_int(r.get("TEAM_ID")): r for r in advanced}
    pts = {to_int(r.get("TEAM_ID")): r for r in base}
    out = []
    for s in standings:
        tid = to_int(s.get("TeamID"))
        a, b = adv.get(tid, {}), pts.get(tid, {})
        out.append(
            {
                "team_id": tid,
                "season": season,
                "season_type": season_type,
                "wins": to_int(s.get("WINS")) or 0,
                "losses": to_int(s.get("LOSSES")) or 0,
                "conf_rank": to_int(s.get("PlayoffRank")),
                "div_rank": to_int(s.get("DivisionRank")),
                "league_rank": to_int(s.get("LeagueRank")),
                "games_back": to_float(s.get("ConferenceGamesBack")),
                "streak": (s.get("strCurrentStreak") or "").strip() or None,
                "last_ten": (s.get("L10") or "").strip() or None,
                "home_record": s.get("HOME") or None,
                "road_record": s.get("ROAD") or None,
                "pts_pg": to_float(s.get("PointsPG")) or to_float(b.get("PTS")),
                "opp_pts_pg": to_float(s.get("OppPointsPG")),
                "off_rating": to_float(a.get("OFF_RATING")),
                "def_rating": to_float(a.get("DEF_RATING")),
                "net_rating": to_float(a.get("NET_RATING")),
                "pace": to_float(a.get("PACE")),
            }
        )
    return out


def team_conference_rows(standings: list[dict]) -> list[dict]:
    return [
        {"id": to_int(s["TeamID"]), "conference": s.get("Conference") or None, "division": s.get("Division") or None}
        for s in standings
    ]


# ---- Awards ----------------------------------------------------------------


def award_rows(awards: list[dict], source: str) -> list[dict]:
    out = []
    for a in awards:
        out.append(
            {
                "player_id": to_int(a["PERSON_ID"]),
                "award": (a.get("DESCRIPTION") or "").strip(),
                "season": a.get("SEASON") or "",
                "team_label": (str(a["ALL_NBA_TEAM_NUMBER"]) if a.get("ALL_NBA_TEAM_NUMBER") not in (None, "") else None),
                "month": _clean_date_str(a.get("MONTH")),
                "week": _clean_date_str(a.get("WEEK")),
                "conference": a.get("CONFERENCE") or None,
                "description": a.get("TYPE") or None,
                "source": source,
            }
        )
    return [r for r in out if r["award"] and r["season"]]


def _clean_date_str(v) -> str | None:
    d = to_date(v)
    return d.isoformat() if d else None


# ---- ESPN ------------------------------------------------------------------


def news_rows(payload: dict, team_ids_by_espn: dict[str, int], player_ids_by_name: dict[str, int]) -> list[dict]:
    out = []
    for art in payload.get("articles", []):
        url = ((art.get("links") or {}).get("web") or {}).get("href")
        published = to_datetime(art.get("published"))
        if not url or not art.get("headline") or not published:
            continue
        players, teams = set(), set()
        for c in art.get("categories") or []:
            if c.get("type") == "team" and str(c.get("teamId")) in team_ids_by_espn:
                teams.add(team_ids_by_espn[str(c["teamId"])])
            if c.get("type") == "athlete":
                pid = player_ids_by_name.get((c.get("description") or "").strip().lower())
                if pid:
                    players.add(pid)
        images = art.get("images") or []
        out.append(
            {
                "id": str(art.get("id") or art.get("dataSourceIdentifier") or hashlib.sha1(url.encode()).hexdigest()),
                "headline": art["headline"].strip(),
                "description": (art.get("description") or "").strip() or None,
                "url": url,
                "image_url": images[0].get("url") if images else None,
                "published_at": published,
                "byline": art.get("byline") or None,
                "player_ids": sorted(players),
                "team_ids": sorted(teams),
                "source": "ESPN",
            }
        )
    return out


def scoreboard_rows(payload: dict, team_ids_by_abbr: dict[str, int], season: str) -> list[dict]:
    """ESPN scoreboard events as game rows. ESPN ids are kept for matching; NBA ids are resolved later."""
    state_map = {"pre": "scheduled", "in": "live", "post": "final"}
    out = []
    for ev in payload.get("events", []):
        comp = (ev.get("competitions") or [{}])[0]
        sides = {c.get("homeAway"): c for c in comp.get("competitors", [])}
        if "home" not in sides or "away" not in sides:
            continue
        home = team_ids_by_abbr.get(nba_abbr(sides["home"]["team"]["abbreviation"]))
        away = team_ids_by_abbr.get(nba_abbr(sides["away"]["team"]["abbreviation"]))
        if not home or not away:
            continue  # All-Star and exhibition teams
        st = (ev.get("status") or {}).get("type") or {}
        status = state_map.get(st.get("state"), "scheduled")
        if st.get("name") == "STATUS_POSTPONED":
            status = "postponed"
        tipoff = to_datetime(ev.get("date"))
        out.append(
            {
                "espn_id": str(ev["id"]),
                "season": season,
                "game_date": tipoff.astimezone(EASTERN).date() if tipoff else None,
                "tipoff": tipoff,
                "home_team_id": home,
                "away_team_id": away,
                "home_score": to_int(sides["home"].get("score")) if status != "scheduled" else None,
                "away_score": to_int(sides["away"].get("score")) if status != "scheduled" else None,
                "status": status,
                "status_detail": st.get("shortDetail") or None,
            }
        )
    return out


def bdl_game_rows(games: Iterable[dict], team_ids_by_abbr: dict[str, int], season: str) -> list[dict]:
    """balldontlie games, shaped like scoreboard rows so the same matcher can apply them."""
    out = []
    for g in games:
        home = team_ids_by_abbr.get((g.get("home_team") or {}).get("abbreviation", ""))
        away = team_ids_by_abbr.get((g.get("visitor_team") or {}).get("abbreviation", ""))
        if not home or not away:
            continue
        raw = str(g.get("status") or "")
        status = "final" if raw.lower().startswith("final") else ("live" if g.get("period") else "scheduled")
        tipoff = to_datetime(g.get("datetime"))
        out.append(
            {
                "espn_id": None,
                "season": season,
                "game_date": to_date(g.get("date")),
                "tipoff": tipoff,
                "home_team_id": home,
                "away_team_id": away,
                "home_score": to_int(g.get("home_team_score")) if status != "scheduled" else None,
                "away_score": to_int(g.get("visitor_team_score")) if status != "scheduled" else None,
                "status": status,
                "status_detail": raw or None,
            }
        )
    return out

