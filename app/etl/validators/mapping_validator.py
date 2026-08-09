from dataclasses import dataclass

from app.etl.parser.formula_parser import extract_placeholders
from app.schemas.mapping import MappingRule, Operation
from app.schemas.template import TemplateDetail

_SINGLE_SOURCE_OPERATIONS = (
    Operation.COPY,
    Operation.TRIM,
    Operation.UPPERCASE,
    Operation.LOWERCASE,
    Operation.REPLACE,
    Operation.DATE_FORMAT,
)


@dataclass
class MappingError:
    destination: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"destination": self.destination, "message": self.message}


def validate_mappings(
    mappings: list[MappingRule], template: TemplateDetail, upload_columns: list[str]
) -> list[MappingError]:
    """Business-rule validation beyond Pydantic: destinations, sources, and per-operation arity."""
    errors: list[MappingError] = []
    seen_destinations: set[str] = set()
    upload_columns_set = set(upload_columns)

    for rule in mappings:
        if rule.destination not in template.columns:
            errors.append(
                MappingError(rule.destination, f"'{rule.destination}' is not a column on template '{template.id}'")
            )
            continue

        if rule.destination in seen_destinations:
            errors.append(MappingError(rule.destination, "Duplicate mapping for this destination"))
        seen_destinations.add(rule.destination)

        for source in rule.sources:
            if source not in upload_columns_set:
                errors.append(MappingError(rule.destination, f"Unknown source column '{source}'"))

        if rule.operation in _SINGLE_SOURCE_OPERATIONS and len(rule.sources) != 1:
            errors.append(
                MappingError(rule.destination, f"'{rule.operation.value}' requires exactly 1 source column")
            )
        elif rule.operation == Operation.CONCATENATE and len(rule.sources) < 2:
            errors.append(MappingError(rule.destination, "Concatenate requires at least 2 source columns"))
        elif rule.operation == Operation.MULTIPLY and len(rule.sources) < 1:
            errors.append(MappingError(rule.destination, "Multiply requires at least 1 source column"))
        elif rule.operation == Operation.CONSTANT and "value" not in rule.options:
            errors.append(MappingError(rule.destination, "Constant operation requires options.value"))
        elif rule.operation == Operation.FORMULA:
            if not rule.formula:
                errors.append(MappingError(rule.destination, "Formula operation requires a 'formula' string"))
            else:
                for placeholder in extract_placeholders(rule.formula):
                    if placeholder not in upload_columns_set:
                        errors.append(
                            MappingError(rule.destination, f"Formula references unknown column '{placeholder}'")
                        )

    for column in template.required_columns:
        if column not in seen_destinations:
            errors.append(MappingError(column, "Required destination column is not mapped"))

    return errors
