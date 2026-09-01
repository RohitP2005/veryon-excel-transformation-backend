import re
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.config import settings
from app.core.exceptions import TemplateNotFoundError
from app.etl.readers.excel_reader import read_excel_preview
from app.models.custom_template_store import custom_template_store
from app.models.template_registry import template_registry
from app.schemas.template import TemplateDetail, TemplateSummary

router = APIRouter(prefix="/api/templates", tags=["templates"])

# .xlsx files are zip archives; validating this magic number rejects non-Excel content
# regardless of the extension/MIME type the client claims.
_XLSX_ZIP_MAGIC = b"PK\x03\x04"


@router.get("", response_model=list[TemplateSummary])
def list_templates() -> list[TemplateSummary]:
    all_templates = template_registry.list() + custom_template_store.list()
    return [
        TemplateSummary(id=t.id, name=t.name, description=t.description, sheet_name=t.sheet_name)
        for t in all_templates
    ]


@router.get("/{template_id}", response_model=TemplateDetail)
def get_template(template_id: str) -> TemplateDetail:
    template = template_registry.get(template_id) or custom_template_store.get(template_id)
    if template is None:
        raise TemplateNotFoundError(template_id)
    return template


@router.post("", response_model=TemplateDetail, status_code=201)
async def create_template(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(""),
    sheet_name: str | None = Form(None),
    header_row: int = Form(1),
    header_row_start: int | None = Form(None),
) -> TemplateDetail:
    """Add a new template by uploading a sample workbook - its header row becomes the
    template's columns; name/description/sheet_name are supplied by the user."""
    clean_name = name.strip()
    if not clean_name:
        raise HTTPException(status_code=422, detail="name is required")
    if not file.filename or not file.filename.lower().endswith(settings.allowed_upload_extensions):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported")
    if header_row < 1:
        raise HTTPException(status_code=400, detail="header_row must be 1 or greater")

    contents = await file.read()
    if len(contents) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=400, detail="File exceeds maximum allowed size")
    if not contents.startswith(_XLSX_ZIP_MAGIC):
        raise HTTPException(status_code=400, detail="File content is not a valid Excel workbook")

    tmp_path = settings.upload_dir / f"template-{uuid.uuid4()}.xlsx"
    tmp_path.write_bytes(contents)
    try:
        columns, _, _ = read_excel_preview(
            tmp_path, sample_rows=1, header_row=header_row, header_row_start=header_row_start
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Uploaded file could not be read as an Excel workbook") from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    if not columns:
        raise HTTPException(status_code=400, detail="No columns were detected in the uploaded file")

    existing_ids = {t.id for t in template_registry.list()} | {t.id for t in custom_template_store.list()}
    template = TemplateDetail(
        id=_unique_slug(clean_name, existing_ids),
        name=clean_name,
        description=description.strip(),
        sheet_name=(sheet_name or clean_name).strip() or clean_name,
        columns=columns,
        required_columns=[],
        output_format=_default_output_format(columns),
    )
    return custom_template_store.create(template)


def _unique_slug(name: str, existing_ids: set[str]) -> str:
    base = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "template"
    slug = base
    suffix = 2
    while slug in existing_ids:
        slug = f"{base}_{suffix}"
        suffix += 1
    return slug


def _default_output_format(columns: list[str]) -> dict:
    return {
        "header_style": {"bold": True, "fill": "D9E1F2"},
        "column_widths": {c: max(12, min(40, len(c) + 2)) for c in columns},
    }
