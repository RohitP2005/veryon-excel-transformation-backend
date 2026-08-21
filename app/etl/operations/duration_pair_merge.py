from typing import Any

from app.etl.operations._duration import format_duration


class DurationPairMergeOperation:
    """One-shot "TSN/CSN" style transform: extract TSN, format as H:MM, append a suffix;
    extract CSN, append its own suffix; merge both into one field with a separator.

    sources = [tsn_column, csn_column]. Example (all defaults): TSN=12530, CSN=4321
    -> "12530:00 FH, 4321 FC".
    """

    def execute(self, values: list[Any], *, options: dict[str, Any]) -> Any:
        first = values[0] if len(values) > 0 else None
        second = values[1] if len(values) > 1 else None

        separator = options.get("separator", ", ")
        first_suffix = options.get("first_suffix", " FH")
        second_suffix = options.get("second_suffix", " FC")

        parts: list[str] = []
        if first is not None and str(first) != "":
            parts.append(f"{format_duration(first)}{first_suffix}")
        if second is not None and str(second) != "":
            parts.append(f"{second}{second_suffix}")

        return separator.join(parts)
