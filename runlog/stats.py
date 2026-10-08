"""Read-side helpers: input parsing, formatting runs, and building summaries."""
from collections import Counter
from datetime import date, timedelta

from runlog.runs import VALID_UNITS, RunValidationError, format_pace


def parse_unit(value) -> str:
    """Return 'mi' or 'km' (default 'mi')."""
    unit = str(value or "mi").lower()
    if unit not in VALID_UNITS:
        raise RunValidationError(f"Unit '{value}' must be 'mi' or 'km'.")
    return unit


def parse_limit(value, default: int = 5, maximum: int = 50) -> int:
    """Return how many runs to list (default 5, max 50)."""
    if value is None:
        return default
    try:
        limit = int(value)
    except (TypeError, ValueError):
        raise RunValidationError("Limit must be a whole number.") from None
    if not 1 <= limit <= maximum:
        raise RunValidationError(f"Limit must be between 1 and {maximum}.")
    return limit


def parse_day(value) -> date:
    """Return the given YYYY-MM-DD date, or today if none is given."""
    if not value:
        return date.today()
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        raise RunValidationError(f"Date '{value}' must be in YYYY-MM-DD format.") from None


def format_duration(seconds: int) -> str:
    """Return '42:30' or '1:05:10'."""
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def describe_run(run: dict, unit: str = "mi") -> dict:
    """Convert a stored run (metric) into a readable summary in the requested unit."""
    return {
        "id": run["id"],
        "date": run["date"],
        "distance": round(run["distanceMeters"] / VALID_UNITS[unit], 2),
        "unit": unit,
        "duration": format_duration(run["durationSeconds"]),
        "pace": format_pace(run["durationSeconds"], run["distanceMeters"], unit),
        "runType": run["runType"],
        "effort": run["effort"],
        "notes": run["notes"],
    }


def recent_runs(runs: list[dict], limit: int, unit: str) -> list[dict]:
    """Return the newest runs first, up to `limit`."""
    newest_first = sorted(runs, key=lambda run: run["date"], reverse=True)
    return [describe_run(run, unit) for run in newest_first[:limit]]


def week_bounds(any_day: date) -> tuple[date, date]:
    """Return the Monday and Sunday of the week containing `any_day`."""
    start = any_day - timedelta(days=any_day.weekday())
    return start, start + timedelta(days=6)


def summarize_week(runs: list[dict], any_day: date, unit: str) -> dict:
    """Totals for the Monday-to-Sunday week containing `any_day`."""
    start, end = week_bounds(any_day)
    in_week = [run for run in runs if start <= date.fromisoformat(run["date"]) <= end]

    summary = {"weekStart": start.isoformat(), "weekEnd": end.isoformat(), "runCount": len(in_week)}
    if not in_week:
        return summary

    total_meters = sum(run["distanceMeters"] for run in in_week)
    total_seconds = sum(run["durationSeconds"] for run in in_week)
    longest = max(in_week, key=lambda run: run["distanceMeters"])

    summary.update({
        "totalDistance": round(total_meters / VALID_UNITS[unit], 2),
        "unit": unit,
        "totalTime": format_duration(total_seconds),
        "averagePace": format_pace(total_seconds, total_meters, unit),
        "longestRun": describe_run(longest, unit),
        "runsByType": dict(Counter(run["runType"] for run in in_week)),
    })
    return summary