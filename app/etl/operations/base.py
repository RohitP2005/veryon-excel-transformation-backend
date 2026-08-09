from typing import Any, Protocol


class BaseOperation(Protocol):
    """Every ETL operation turns one or more source values into a single output value."""

    def execute(self, values: list[Any], *, options: dict[str, Any]) -> Any: ...
