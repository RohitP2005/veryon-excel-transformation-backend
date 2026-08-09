from app.etl.validators.mapping_validator import validate_mappings
from app.schemas.mapping import MappingRule, Operation
from app.schemas.template import TemplateDetail

TEMPLATE = TemplateDetail(
    id="customer_import",
    name="Customer Import",
    description="test",
    sheet_name="Customers",
    columns=["Customer ID", "Customer Name", "Email", "Address"],
    required_columns=["Customer ID", "Customer Name"],
)

UPLOAD_COLUMNS = ["ID", "Name", "Mail", "Addr1", "Addr2"]


def test_valid_mapping_has_no_errors():
    mappings = [
        MappingRule(destination="Customer ID", sources=["ID"], operation=Operation.COPY),
        MappingRule(destination="Customer Name", sources=["Name"], operation=Operation.COPY),
        MappingRule(destination="Email", sources=["Mail"], operation=Operation.COPY),
        MappingRule(destination="Address", sources=["Addr1", "Addr2"], operation=Operation.CONCATENATE),
    ]
    assert validate_mappings(mappings, TEMPLATE, UPLOAD_COLUMNS) == []


def test_missing_required_destination_is_reported():
    mappings = [MappingRule(destination="Email", sources=["Mail"], operation=Operation.COPY)]
    errors = validate_mappings(mappings, TEMPLATE, UPLOAD_COLUMNS)
    messages = [e.message for e in errors]
    assert any("Required destination column" in m for m in messages)


def test_unknown_source_column_is_reported():
    mappings = [
        MappingRule(destination="Customer ID", sources=["Unknown"], operation=Operation.COPY),
        MappingRule(destination="Customer Name", sources=["Name"], operation=Operation.COPY),
    ]
    errors = validate_mappings(mappings, TEMPLATE, UPLOAD_COLUMNS)
    assert any("Unknown source column" in e.message for e in errors)


def test_concatenate_requires_two_sources():
    mappings = [
        MappingRule(destination="Customer ID", sources=["ID"], operation=Operation.COPY),
        MappingRule(destination="Customer Name", sources=["Name"], operation=Operation.COPY),
        MappingRule(destination="Address", sources=["Addr1"], operation=Operation.CONCATENATE),
    ]
    errors = validate_mappings(mappings, TEMPLATE, UPLOAD_COLUMNS)
    assert any("at least 2 source columns" in e.message for e in errors)


def test_duplicate_destination_is_reported():
    mappings = [
        MappingRule(destination="Customer ID", sources=["ID"], operation=Operation.COPY),
        MappingRule(destination="Customer ID", sources=["Name"], operation=Operation.COPY),
        MappingRule(destination="Customer Name", sources=["Name"], operation=Operation.COPY),
    ]
    errors = validate_mappings(mappings, TEMPLATE, UPLOAD_COLUMNS)
    assert any("Duplicate mapping" in e.message for e in errors)
