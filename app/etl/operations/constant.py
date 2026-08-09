from typing import Any


class ConstantOperation:
    def execute(self, values: list[Any], *, options: dict[str, Any]) -> Any:
        return options.get("value")
