"""Run data: validation, unit conversion, and pace calculation."""
import uuid
from datetime import date

METERS_PER_MILE = 1609.344
METERS_PER_KM = 1000.0
VALID_UNITS = {"mi": METERS_PER_MILE, "km": METERS_PER_KM}
VALID_RUN_TYPES = {"easy", "tempo", "long", "race"}
MAX_NOTES_LENGTH = 500


class RunValidationError(ValueError):
    """Raised when run input is invalid."""


def parse_duration(text: str) -> int:
    """Convert 'mm:ss' or 'h:mm:ss' into total seconds."""
    parts = str(text).strip().split(":")
    if len(parts) not in (2, 3) or not all(p.isdigit() for p in parts):
        raise RunValidationError(
            f"Duration '{text}' must look like mm:ss or h:mm:ss, e.g. '42:30'."
        )
    numbers = [int(p) for p in parts]
    if len(numbers) == 2:
        numbers.insert(0, 0)
    hours, minutes, seconds = numbers
    if seconds >= 60 or (len(parts) == 3 and minutes >= 60):
        raise RunValidationError(f"Duration '{text}' has invalid minutes or seconds.")
    total = hours * 3600 + minutes * 60 + seconds
    if total <= 0:
        raise RunValidationError("Duration must be greater than zero.")
    return total


def to_meters(distance: float, unit: str) -> int:
    """Convert a distance in miles or km to whole meters."""
    if unit not in VALID_UNITS:
        raise RunValidationError(f"Unit '{unit}' must be 'mi' or 'km'.")
    if distance <= 0:
        raise RunValidationError("Distance must be greater than zero.")
    return round(distance * VALID_UNITS[unit])


def format_pace(duration_seconds: int, distance_meters: int, unit: str = "mi") -> str:
    """Return pace like '8:15 /mi'."""
    seconds_per_unit = duration_seconds / (distance_meters / VALID_UNITS[unit])
    minutes, seconds = divmod(round(seconds_per_unit), 60)
    return f"{minutes}:{seconds:02d} /{unit}"


def build_run(args: dict, user_id: str) -> dict:
    """Validate raw tool arguments and return a run document in metric units."""
    run_date = args.get("date") or date.today().isoformat()
    try:
        date.fromisoformat(run_date)
    except ValueError:
        raise RunValidationError(f"Date '{run_date}' must be in YYYY-MM-DD format.") from None

    if args.get("distance") is None:
        raise RunValidationError("Distance is required.")
    try:
        distance = float(args["distance"])
    except (TypeError, ValueError):
        raise RunValidationError(f"Distance '{args['distance']}' must be a number.") from None

    if not args.get("duration"):
        raise RunValidationError("Duration is required.")

    unit = str(args.get("unit") or "mi").lower()
    run_type = str(args.get("run_type") or "easy").lower()
    if run_type not in VALID_RUN_TYPES:
        raise RunValidationError(
            f"Run type '{run_type}' must be one of: {', '.join(sorted(VALID_RUN_TYPES))}."
        )

    effort = args.get("effort")
    if effort is not None:
        try:
            effort = int(effort)
        except (TypeError, ValueError):
            raise RunValidationError("Effort must be a whole number from 1 to 10.") from None
        if not 1 <= effort <= 10:
            raise RunValidationError("Effort must be between 1 and 10.")

    notes = str(args.get("notes") or "").strip()
    if len(notes) > MAX_NOTES_LENGTH:
        raise RunValidationError(f"Notes must be {MAX_NOTES_LENGTH} characters or fewer.")

    return {
        "id": str(uuid.uuid4()),
        "userId": user_id,
        "date": run_date,
        "distanceMeters": to_meters(distance, unit),
        "durationSeconds": parse_duration(args["duration"]),
        "runType": run_type,
        "effort": effort,
        "notes": notes,
    }