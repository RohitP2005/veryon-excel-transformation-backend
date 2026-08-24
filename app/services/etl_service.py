"""Orchestrates the read -> validate -> transform -> write pipeline for a generate request."""
import uuid
from pathlib import Path

import pandas as pd
from loguru import logger

from app.core.config import settings
from app.core.exceptions import MappingValidationError, TemplateNotFoundError, UploadNotFoundError
from app.etl.operations.registry import get_operation
from app.etl.readers.excel_reader import read_excel_records
from app.etl.validators.mapping_validator import validate_mappings
from app.etl.writers.excel_writer import write_excel
from app.models.template_registry import template_registry
from app.models.upload_store import upload_store
from app.schemas.mapping import GenerateRequest, Operation


def generate_output(request: GenerateRequest) -> tuple[str, Path, str]:
    template = template_registry.get(request.template_id)
    if template is None:
        raise TemplateNotFoundError(request.template_id)

    upload = upload_store.get(request.upload_id)
    if upload is None:
        raise UploadNotFoundError(request.upload_id)

    errors = validate_mappings(request.mappings, template, upload.columns)
    if errors:
        raise MappingValidationError([e.to_dict() for e in errors])

    _, rows = read_excel_records(upload.file_path, upload.header_row, upload.header_row_start)
    output_columns: dict[str, list] = {}

    for rule in request.mappings:
        operation = get_operation(rule.operation)
        base_options = dict(rule.options)
        if rule.operation == Operation.FORMULA:
            base_options["formula"] = rule.formula

        # Row-wise execution keeps every operation (including formulas needing full-row
        # context) behind one simple interface; swap for vectorized ops if perf matters.
        values = [
            operation.execute([row.get(col) for col in rule.sources], options={**base_options, "row": row})
            for row in rows
        ]
        output_columns[rule.destination] = values

    # Mapping a required column is optional now (see mapping_validator) - any template column
    # the user didn't map at all still appears in the output, just blank, instead of blocking.
    row_count = len(rows)
    for column in template.columns:
        output_columns.setdefault(column, [None] * row_count)

    output_df = pd.DataFrame(output_columns)
    ordered_columns = [c for c in template.columns if c in output_df.columns]
    output_df = output_df[ordered_columns]

    job_id = str(uuid.uuid4())
    output_path = settings.output_dir / f"{job_id}.xlsx"
    write_excel(output_df, output_path, template.sheet_name, template.output_format)
    output_filename = f"{template.name.replace(' ', '')}_Output.xlsx"

    logger.info(
        "Generated output workbook job_id={} rows={} columns={}",
        job_id,
        len(output_df),
        len(output_df.columns),
    )
    return job_id, output_path, output_filename

