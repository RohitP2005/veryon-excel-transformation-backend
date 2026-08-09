from typing import Any


class TrimOperation:
    def execute(self, values: list[Any], *, options: dict[str, Any]) -> Any:
        value = values[0] if values else None
        return value.strip() if isinstance(value, str) else value
