from typing import Any

from pydantic import BaseModel


class UploadResponse(BaseModel):
    upload_id: str
    file_name: str
    columns: list[str]
    sample_rows: list[dict[str, Any]]
    row_count: int
    header_row: int
