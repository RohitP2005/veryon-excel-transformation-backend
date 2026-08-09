from typing import Any

from pydantic import BaseModel, Field


class TemplateSummary(BaseModel):
    id: str
    name: str
    description: str
    sheet_name: str


class TemplateDetail(TemplateSummary):
    columns: list[str]
    required_columns: list[str] = Field(default_factory=list)
    output_format: dict[str, Any] = Field(default_factory=dict)
