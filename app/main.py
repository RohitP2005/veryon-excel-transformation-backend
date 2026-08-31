from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.api import formulas, generate, health, templates, upload
from app.core.config import settings
from app.core.exceptions import (
    ETLOperationError,
    JobNotFoundError,
    MappingValidationError,
    SavedFormulaNotFoundError,
    TemplateNotFoundError,
    UploadNotFoundError,
)
from app.core.logging import RequestIDMiddleware, configure_logging
from app.etl.parser.formula_parser import FormulaError

configure_logging()

app = FastAPI(
    title="Excel Transformation Tool API",
    description="ETL API for mapping and transforming customer Excel files into standardized templates.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Custom response headers are hidden from browser JS unless explicitly exposed.
    expose_headers=["X-Job-Id", "Content-Disposition"],
)
app.add_middleware(RequestIDMiddleware)

app.include_router(health.router)
app.include_router(templates.router)
app.include_router(upload.router)
app.include_router(generate.router)
app.include_router(formulas.router)


@app.exception_handler(MappingValidationError)
async def mapping_validation_error_handler(request: Request, exc: MappingValidationError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": "Mapping validation failed", "errors": exc.errors})


@app.exception_handler(TemplateNotFoundError)
async def template_not_found_handler(request: Request, exc: TemplateNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(UploadNotFoundError)
async def upload_not_found_handler(request: Request, exc: UploadNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(JobNotFoundError)
async def job_not_found_handler(request: Request, exc: JobNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(SavedFormulaNotFoundError)
async def saved_formula_not_found_handler(request: Request, exc: SavedFormulaNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(FormulaError)
async def formula_error_handler(request: Request, exc: FormulaError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(ETLOperationError)
async def etl_operation_error_handler(request: Request, exc: ETLOperationError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
