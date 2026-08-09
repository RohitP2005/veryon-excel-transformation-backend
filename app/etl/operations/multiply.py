from typing import Any


class MultiplyOperation:
    def execute(self, values: list[Any], *, options: dict[str, Any]) -> Any:
        result = 1.0
        for value in values:
            result *= float(value) if value is not None else 0.0
        return result
