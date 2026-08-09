from typing import Any


class CopyOperation:
    def execute(self, values: list[Any], *, options: dict[str, Any]) -> Any:
        return values[0] if values else None
