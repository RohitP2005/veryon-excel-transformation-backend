from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.exceptions import JobNotFoundError
from app.schemas.mapping import GenerateRequest
from app.services.etl_service import generate_output

router = APIRouter(prefix="/api", tags=["generate"])

_XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.post("/generate")
def generate(request: GenerateRequest) -> FileResponse:
    job_id, output_path, output_filename = generate_output(request)
    return FileResponse(
        path=output_path,
        filename=output_filename,
        media_type=_XLSX_MEDIA_TYPE,
        headers={"X-Job-Id": job_id},
    )


@router.get("/download/{job_id}")
def download(job_id: str) -> FileResponse:
    output_path = settings.output_dir / f"{job_id}.xlsx"
    if not output_path.exists():
        raise JobNotFoundError(job_id)
    return FileResponse(path=output_path, filename="Output.xlsx", media_type=_XLSX_MEDIA_TYPE)
