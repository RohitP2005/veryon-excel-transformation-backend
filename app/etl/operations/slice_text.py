from typing import Any


class SliceOperation:
    """Trims whitespace (by default) then slices a substring of a single value.

    options["length"]: positive counts from the start, negative counts from the end. Missing/
    blank length returns the (optionally trimmed) value unsliced.
    options["retain"] (default True): when True, `length` characters are KEPT from that end
    (e.g. length=4 keeps the first 4 characters like Excel LEFT, length=-4 keeps the last 4 like
    RIGHT). When False, `length` characters are REMOVED from that end instead, keeping the rest
    (length=4 drops the first 4 characters, length=-4 drops the last 4).
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

        if options.get("retain", True):
            return text[:length] if length >= 0 else text[length:]
        return text[length:] if length >= 0 else text[:length]
