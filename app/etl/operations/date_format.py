from datetime import datetime
from typing import Any


class DateFormatOperation:
    def execute(self, values: list[Any], *, options: dict[str, Any]) -> Any:
        value = values[0] if values else None
        if value is None:
            return None
        fmt = options.get("format", "%Y-%m-%d")
        if isinstance(value, datetime):
            return value.strftime(fmt)
        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value)
            except ValueError:
                return value
            return parsed.strftime(fmt)
        return value
