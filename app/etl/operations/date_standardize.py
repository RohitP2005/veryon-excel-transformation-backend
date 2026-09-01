from datetime import date, datetime
from typing import Any

# Fixed English abbreviations, independent of the server's locale (unlike strftime's %b).
_MONTH_ABBREVIATIONS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]  # fmt: skip

# Tried in order; dd-before-mm is checked before mm-before-dd so an unambiguous "13/04/2005"
# (day > 12) still resolves as 13 Apr rather than falling through to a wrong mm/dd/yyyy read.
_CANDIDATE_FORMATS = [
    "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d",
    "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y",
    "%m-%d-%Y", "%m/%d/%Y",
    "%d %b %Y", "%d %B %Y", "%d-%b-%Y",
    "%b %d, %Y", "%B %d, %Y", "%b %d %Y", "%B %d %Y",
]  # fmt: skip


def _format_standard(value: date) -> str:
    return f"{value.day:02d}-{_MONTH_ABBREVIATIONS[value.month - 1]}-{value.year:04d}"


class DateStandardizeOperation:
    """Parses a date in (almost) any common format - dd/mm/yyyy, yyyy-mm-dd, dd-Mon-yyyy, an
    Excel-native datetime, etc. - and re-formats it consistently as "dd-Mon-yyyy"
    (e.g. 13/04/2005 -> 13-Apr-2005). Values that can't be parsed as a date are left unchanged.
    """

    def execute(self, values: list[Any], *, options: dict[str, Any]) -> Any:
        value = values[0] if values else None
        if value is None:
            return None

        if isinstance(value, datetime):
            return _format_standard(value)
        if isinstance(value, date):
            return _format_standard(value)

        text = str(value).strip()
        if not text:
            return None

        try:
            return _format_standard(datetime.fromisoformat(text))
        except ValueError:
            pass

        for fmt in _CANDIDATE_FORMATS:
            try:
                # Naive on purpose - only the date components are ever read; no tzinfo needed.
                return _format_standard(datetime.strptime(text, fmt))  # noqa: DTZ007
            except ValueError:
                continue

        return value
