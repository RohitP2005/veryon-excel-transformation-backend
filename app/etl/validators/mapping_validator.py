from dataclasses import dataclass

from app.etl.parser.formula_parser import extract_placeholders
from app.schemas.mapping import MappingRule, Operation
from app.schemas.template import TemplateDetail


@dataclass
class MappingError:
    destination: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"destination": self.destination, "message": self.message}


def validate_mappings(
    mappings: list[MappingRule], template: TemplateDetail, upload_columns: list[str]
) -> list[MappingError]:
    """Business-rule validation beyond Pydantic.

    Deliberately permissive about *missing* sources: a customer file not having a column for
    some destination (even a "required" one) must not block generation - that column is simply
    left blank in the output (see etl_service). What's still validated are actual mistakes the
    user can fix: unknown destinations/sources, duplicate mappings, and incomplete operation
    configuration (e.g. picking "formula" but leaving it empty).
    """
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

        if rule.operation == Operation.CONSTANT and not str(rule.options.get("value", "")).strip():
            errors.append(MappingError(rule.destination, "Constant operation requires options.value"))
        elif rule.operation == Operation.REPLACE and not str(rule.options.get("find", "")):
            errors.append(MappingError(rule.destination, "Replace operation requires options.find"))
        elif rule.operation == Operation.DATE_FORMAT and not str(rule.options.get("format", "")).strip():
            errors.append(MappingError(rule.destination, "Date format operation requires options.format"))
        elif rule.operation == Operation.FORMULA:
            if not rule.formula:
                errors.append(MappingError(rule.destination, "Formula operation requires a 'formula' string"))
            else:
                for placeholder in extract_placeholders(rule.formula):
                    if placeholder not in upload_columns_set:
                        errors.append(
                            MappingError(rule.destination, f"Formula references unknown column '{placeholder}'")
                        )

    return errors

