"""Shared numeric-hours -> "H:MM" formatting used by DurationFormatOperation and Concatenate."""
from typing import Any


def format_duration(value: Any) -> Any:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if ":" in text:
        return text  # already formatted (e.g. "12530:00")
    try:
        hours_float = float(text)
    except ValueError:
        return value

    whole_hours = int(hours_float)
    minutes = round((hours_float - whole_hours) * 60)
    if minutes == 60:
        whole_hours += 1
        minutes = 0
    return f"{whole_hours}:{minutes:02d}"
