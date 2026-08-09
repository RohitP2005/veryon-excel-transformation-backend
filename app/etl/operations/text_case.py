from typing import Any


class UppercaseOperation:
    def execute(self, values: list[Any], *, options: dict[str, Any]) -> Any:
        value = values[0] if values else None
        return value.upper() if isinstance(value, str) else value


class LowercaseOperation:
    def execute(self, values: list[Any], *, options: dict[str, Any]) -> Any:
        value = values[0] if values else None
        return value.lower() if isinstance(value, str) else value
