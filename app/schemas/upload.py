from typing import Any

from pydantic import BaseModel


class UploadResponse(BaseModel):
    upload_id: str
    file_name: str
    columns: list[str]
    sample_rows: list[dict[str, Any]]
    row_count: int
    header_row: int
    # Set when the caller supplied a header row range: the row the higher-order group headers
    # start on. header_row is still the bottom-most row (the real field names).
    header_row_start: int | None = None
    # Whole-sheet grid (spreadsheet-style "A"/"B"/"C" columns), independent of header_row - lets
    # the frontend's constant-value cell picker show the entire sheet, not just the parsed data.
    grid_columns: list[str]
    grid_rows: list[list[Any]]
