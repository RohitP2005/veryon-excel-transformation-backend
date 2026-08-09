from typing import Any


class ReplaceOperation:
    def execute(self, values: list[Any], *, options: dict[str, Any]) -> Any:
        value = values[0] if values else None
        if not isinstance(value, str):
            return value
        return value.replace(options.get("find", ""), options.get("replace", ""))
