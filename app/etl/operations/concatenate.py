from typing import Any


class ConcatenateOperation:
    def execute(self, values: list[Any], *, options: dict[str, Any]) -> Any:
        separator = options.get("separator", " ")
        parts = [str(v) for v in values if v is not None and str(v) != ""]
        return separator.join(parts)
