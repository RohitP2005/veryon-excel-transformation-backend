from typing import Any


class AppendTextOperation:
    """Prepends/appends fixed text to a value, e.g. turning `12530:00` into `12530:00 FH`.

    When multiple sources are selected, their non-empty values are joined with
    `options["separator"]` (default "") before the prefix/suffix are applied.
    """

    def execute(self, values: list[Any], *, options: dict[str, Any]) -> Any:
        parts = [str(v) for v in values if v is not None and str(v) != ""]
        if not parts:
            return None
        separator = options.get("separator", "")
        prefix = options.get("prefix", "")
        suffix = options.get("suffix", "")
        return f"{prefix}{separator.join(parts)}{suffix}"
