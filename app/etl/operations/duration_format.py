from typing import Any

from app.etl.operations._duration import format_duration


class DurationFormatOperation:
    """Converts a numeric hours value (e.g. 12530 or 12530.5) into "H:MM" (e.g. "12530:00")."""

    def execute(self, values: list[Any], *, options: dict[str, Any]) -> Any:
        value = values[0] if values else None
        return format_duration(value)
