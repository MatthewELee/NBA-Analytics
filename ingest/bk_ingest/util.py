"""Small helpers shared by sources and tasks."""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime
from typing import Any, Iterable


def slugify(name: str) -> str:
    """'Luka Dončić' -> 'luka-doncic'."""
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")


def to_int(v: Any) -> int | None:
    if v is None or v == "":
        return None
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def to_float(v: Any) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def to_date(v: Any) -> date | None:
    """Parses the date formats the NBA and ESPN feeds use."""
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    s = str(v).strip()
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except ValueError:
        pass
    for fmt in ("%b %d, %Y", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y"):
        try:
            return datetime.strptime(s.title() if fmt.startswith("%b") else s, fmt).date()
        except ValueError:
            continue
    return None


def to_datetime(v: Any) -> datetime | None:
    if not v:
        return None
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except ValueError:
        return None


def rows(result_set: dict) -> list[dict]:
    """Turns a stats.nba.com result set ({headers, rowSet} or {headers, data}) into dicts."""
    headers = result_set.get("headers") or []
    data = result_set.get("rowSet", result_set.get("data")) or []
    return [dict(zip(headers, r)) for r in data]


def chunked(items: list, size: int) -> Iterable[list]:
    for i in range(0, len(items), size):
        yield items[i : i + size]
