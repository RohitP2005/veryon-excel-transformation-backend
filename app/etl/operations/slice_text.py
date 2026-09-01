from typing import Any


class SliceOperation:
    """Trims whitespace (by default) then slices a substring of a single value.

    options["length"]: positive takes that many characters from the start (like Excel LEFT),
    negative takes that many characters from the end (like Excel RIGHT). Missing/blank length
    returns the (optionally trimmed) value unsliced.
    options["trim"]: whether to strip whitespace before slicing (default True).
    """

    def execute(self, values: list[Any], *, options: dict[str, Any]) -> Any:
        value = values[0] if values else None
        if value is None:
            return None

        text = str(value)
        if options.get("trim", True):
            text = text.strip()

        raw_length = options.get("length")
        if raw_length in (None, ""):
            return text

        try:
            length = int(float(raw_length))
        except (TypeError, ValueError):
            return text

        return text[:length] if length >= 0 else text[length:]
