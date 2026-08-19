"""Reads customer workbooks via openpyxl directly (no pandas) so we can:

1. Unmerge merged cell ranges and back-fill every cell in the range with the top-left value,
   instead of losing data to blank followers (a common cause of "why is my column empty").
2. Let the caller pick which row is the real header row, instead of always assuming row 1 -
   customer files often have a title/logo row (or several) before the actual headers.
3. Keep blank cells truly blank (Python `None`), never a stray "0"/"nan" placeholder string.
"""
from pathlib import Path
from typing import Any

import openpyxl


def _load_unmerged_worksheet(file_path: Path):
    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb[wb.sheetnames[0]]

    # Merged cells only store their value in the top-left cell; every other cell in the range
    # reads as None via iter_rows. Back-fill the value into every cell before unmerging so no
    # data is lost when the sheet is flattened into rows.
    for merged_range in list(ws.merged_cells.ranges):
        min_col, min_row, max_col, max_row = merged_range.bounds
        top_left_value = ws.cell(row=min_row, column=min_col).value
        ws.unmerge_cells(str(merged_range))
        for row in range(min_row, max_row + 1):
            for col in range(min_col, max_col + 1):
                ws.cell(row=row, column=col, value=top_left_value)

    return ws


def _normalize_cell(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


def _worksheet_to_rows(ws, header_row: int) -> tuple[list[str], list[dict[str, Any]]]:
    all_rows = list(ws.iter_rows(min_row=max(header_row, 1), values_only=True))
    if not all_rows:
        return [], []

    header_cells = all_rows[0]
    columns: list[str] = []
    for i, cell in enumerate(header_cells):
        name = str(cell).strip() if cell not in (None, "") else ""
        columns.append(name or f"Column{i + 1}")

    records: list[dict[str, Any]] = []
    for raw_row in all_rows[1:]:
        # Skip fully-blank trailing rows rather than emitting a row of Nones.
        if all(_normalize_cell(v) is None for v in raw_row):
            continue
        record = {
            columns[i]: _normalize_cell(raw_row[i]) for i in range(len(columns)) if i < len(raw_row)
        }
        records.append(record)

    return columns, records


def read_excel_preview(
    file_path: Path, sample_rows: int = 20, header_row: int = 1
) -> tuple[list[str], list[dict[str, Any]], int]:
    """Return (columns, sample rows, total row count) for an upload preview."""
    ws = _load_unmerged_worksheet(file_path)
    columns, records = _worksheet_to_rows(ws, header_row)
    return columns, records[:sample_rows], len(records)


def read_excel_records(file_path: Path, header_row: int = 1) -> tuple[list[str], list[dict[str, Any]]]:
    """Read the full workbook as (columns, rows) for transformation."""
    ws = _load_unmerged_worksheet(file_path)
    return _worksheet_to_rows(ws, header_row)
