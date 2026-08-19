from typing import Any

from app.etl.operations._duration import format_duration


class ConcatenateOperation:
    """Joins non-empty values with a separator.

    Optionally accepts `options["formats"]`: a list positionally aligned with the sources,
    each entry `{ "prefix": str, "suffix": str, "duration_format": bool }`, applied to that
    source's value before joining (e.g. TSN -> "12530:00 FH", CSN -> "4321 FC" -> "12530:00 FH, 4321 FC").
    """

    def execute(self, values: list[Any], *, options: dict[str, Any]) -> Any:
        separator = options.get("separator", " ")
        formats = options.get("formats") or []

        parts = []
        for i, value in enumerate(values):
            if value is None or str(value) == "":
                continue
            text = str(value)
            fmt = formats[i] if i < len(formats) else {}
            if fmt.get("duration_format"):
                text = str(format_duration(text))
            parts.append(f"{fmt.get('prefix', '')}{text}{fmt.get('suffix', '')}")

        return separator.join(parts)
