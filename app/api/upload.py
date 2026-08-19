import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from loguru import logger

from app.core.config import settings
from app.etl.readers.excel_reader import read_excel_preview
from app.models.upload_store import UploadRecord, upload_store
from app.schemas.upload import UploadResponse

router = APIRouter(prefix="/api", tags=["upload"])

# .xlsx files are zip archives; validating this magic number rejects non-Excel content
# regardless of the extension/MIME type the client claims.
_XLSX_ZIP_MAGIC = b"PK\x03\x04"


@router.post("/upload", response_model=UploadResponse)
async def upload_excel(
    file: UploadFile = File(...),
    header_row: int = Form(1),
) -> UploadResponse:
    _validate_extension(file.filename)
    _validate_header_row(header_row)
    contents = await file.read()
    _validate_size(contents)
    _validate_content(contents)

    upload_id = str(uuid.uuid4())
    destination = settings.upload_dir / f"{upload_id}.xlsx"
    destination.write_bytes(contents)

    try:
        columns, sample_rows, row_count = read_excel_preview(
            destination, settings.sample_row_count, header_row
        )
    except Exception as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Uploaded file could not be read as an Excel workbook") from exc

    upload_store.add(
        UploadRecord(
            upload_id=upload_id,
            file_name=file.filename or "upload.xlsx",
            file_path=destination,
            columns=columns,
            row_count=row_count,
            header_row=header_row,
        )
    )
    logger.info(
        "Upload stored upload_id={} rows={} columns={} header_row={}",
        upload_id,
        row_count,
        len(columns),
        header_row,
    )

    return UploadResponse(
        upload_id=upload_id,
        file_name=file.filename or "upload.xlsx",
        columns=columns,
        sample_rows=sample_rows,
        row_count=row_count,
        header_row=header_row,
    )


def _validate_extension(filename: str | None) -> None:
    if not filename or not filename.lower().endswith(settings.allowed_upload_extensions):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported")


def _validate_header_row(header_row: int) -> None:
    if header_row < 1:
        raise HTTPException(status_code=400, detail="header_row must be 1 or greater")


def _validate_size(contents: bytes) -> None:
    if len(contents) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=400, detail="File exceeds maximum allowed size")


def _validate_content(contents: bytes) -> None:
    if not contents.startswith(_XLSX_ZIP_MAGIC):
        raise HTTPException(status_code=400, detail="File content is not a valid Excel workbook")
