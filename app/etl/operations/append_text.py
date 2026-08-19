from typing import Any


class AppendTextOperation:
    """Prepends/appends fixed text to a value, e.g. turning `12530:00` into `12530:00 FH`."""

    def execute(self, values: list[Any], *, options: dict[str, Any]) -> Any:
        value = values[0] if values else None
        if value is None:
            return None
        prefix = options.get("prefix", "")
        suffix = options.get("suffix", "")
        return f"{prefix}{value}{suffix}"
