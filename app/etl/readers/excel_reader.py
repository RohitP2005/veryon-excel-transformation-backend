from pathlib import Path
from typing import Any

import pandas as pd


def _read_dataframe(file_path: Path) -> pd.DataFrame:
    df = pd.read_excel(file_path, engine="openpyxl")
    df.columns = [str(c) for c in df.columns]
    return df.where(pd.notnull(df), None)


def read_excel_preview(
    file_path: Path, sample_rows: int = 20
) -> tuple[list[str], list[dict[str, Any]], int]:
    """Return (columns, sample rows, total row count) for an upload preview."""
    df = _read_dataframe(file_path)
    columns = list(df.columns)
    row_count = len(df)
    sample = df.head(sample_rows).to_dict(orient="records")
    return columns, sample, row_count


def read_excel_dataframe(file_path: Path) -> pd.DataFrame:
    """Read the full workbook as a DataFrame for transformation."""
    return _read_dataframe(file_path)
