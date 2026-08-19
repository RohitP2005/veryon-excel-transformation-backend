from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class Operation(str, Enum):
    COPY = "copy"
    TRIM = "trim"
    UPPERCASE = "uppercase"
    LOWERCASE = "lowercase"
    CONCATENATE = "concatenate"
    MULTIPLY = "multiply"
    FORMULA = "formula"
    REPLACE = "replace"
    DATE_FORMAT = "date_format"
    CONSTANT = "constant"
    APPEND_TEXT = "append_text"
    DURATION_FORMAT = "duration_format"


class MappingRule(BaseModel):
    destination: str
    sources: list[str] = Field(default_factory=list)
    operation: Operation
    formula: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)

    @field_validator("formula")
    @classmethod
    def formula_required_for_formula_op(cls, v: str | None, info):
        if info.data.get("operation") == Operation.FORMULA and not v:
            raise ValueError("formula is required when operation is 'formula'")
        return v


class GenerateRequest(BaseModel):
    template_id: str
    upload_id: str
    mappings: list[MappingRule]
