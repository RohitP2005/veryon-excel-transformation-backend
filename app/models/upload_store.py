"""In-memory registry of uploaded files for the current process (MVP only, no persistence)."""
from dataclasses import dataclass
from pathlib import Path


@dataclass
class UploadRecord:
    upload_id: str
    file_name: str
    file_path: Path
    columns: list[str]
    row_count: int
    header_row: int = 1


class UploadStore:
    def __init__(self) -> None:
        self._records: dict[str, UploadRecord] = {}

    def add(self, record: UploadRecord) -> None:
        self._records[record.upload_id] = record

    def get(self, upload_id: str) -> UploadRecord | None:
        return self._records.get(upload_id)


upload_store = UploadStore()
