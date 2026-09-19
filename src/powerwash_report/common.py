from __future__ import annotations

from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo


def first(record: dict, *keys, default=None):
    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return value
    return default


def parse_dt(value, tz_name: str = "Pacific/Auckland") -> datetime | None:
    if value in (None, "", 0):
        return None
    tz = ZoneInfo(tz_name)
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, (int, float)):
        dt = datetime.fromtimestamp(value, timezone.utc)
    else:
        text = str(value).strip().replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            for pattern in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    dt = datetime.strptime(text, pattern)
                    break
                except ValueError:
                    continue
            else:
                return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    return dt.astimezone(tz)


def local_day_bounds(day: date, tz_name: str) -> tuple[datetime, datetime]:
    tz = ZoneInfo(tz_name)
    start = datetime.combine(day, time.min, tzinfo=tz)
    end = datetime.combine(day, time.max, tzinfo=tz)
    return start, end


def minutes_between(later: datetime | None, earlier: datetime | None) -> int | None:
    if not later or not earlier:
        return None
    return round((later - earlier).total_seconds() / 60)


def normal_text(value) -> str:
    return " ".join(str(value or "").lower().split())


def address_key(value) -> str:
    return normal_text(value).replace(",", "")

