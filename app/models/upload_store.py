"""Registry of uploaded files for the current process.

Upload metadata is kept in memory for fast access, and also written to a small JSON sidecar file
next to the uploaded workbook. Without that sidecar, restarting the backend process (e.g. every
`uvicorn --reload` reload while editing code, or a real redeploy) would sever the upload_id a
browser tab is holding from the server's memory, even though the actual uploaded file on disk
survives the restart untouched - `get()` falls back to the sidecar so an upload recovers
automatically on first access after a restart, instead of surfacing as "upload not found".
"""
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from app.core.config import settings


@dataclass
class UploadRecord:
    upload_id: str
    file_name: str
    file_path: Path
    columns: list[str]
    row_count: int
    header_row: int = 1
    header_row_start: int | None = None


def _sidecar_path(file_path: Path) -> Path:
    return file_path.with_suffix(".meta.json")


class UploadStore:
    def __init__(self) -> None:
        self._records: dict[str, UploadRecord] = {}

    def add(self, record: UploadRecord) -> None:
        self._records[record.upload_id] = record
        payload = asdict(record)
        payload["file_path"] = str(record.file_path)
        _sidecar_path(record.file_path).write_text(json.dumps(payload), encoding="utf-8")

    def get(self, upload_id: str) -> UploadRecord | None:
        record = self._records.get(upload_id)
        if record is not None:
            return record

        record = self._load_from_disk(upload_id)
        if record is not None:
            self._records[upload_id] = record
        return record

    def _load_from_disk(self, upload_id: str) -> UploadRecord | None:
        sidecar_path = _sidecar_path(settings.upload_dir / f"{upload_id}.xlsx")
        if not sidecar_path.exists():
            return None
        try:
            payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
            payload["file_path"] = Path(payload["file_path"])
        except (OSError, ValueError, KeyError):
            return None
        if not payload["file_path"].exists():
            return None
        return UploadRecord(**payload)


upload_store = UploadStore()
