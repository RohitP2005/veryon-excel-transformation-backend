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


def test_missing_required_destination_is_not_blocking():
    """Required is metadata-only now - an unmapped required column must not error (see etl_service,
    which fills it in blank instead of failing the whole generate request)."""
    mappings = [MappingRule(destination="Email", sources=["Mail"], operation=Operation.COPY)]
    assert validate_mappings(mappings, TEMPLATE, UPLOAD_COLUMNS) == []


def test_unknown_source_column_is_reported():
    mappings = [
        MappingRule(destination="Customer ID", sources=["Unknown"], operation=Operation.COPY),
        MappingRule(destination="Customer Name", sources=["Name"], operation=Operation.COPY),
    ]
    errors = validate_mappings(mappings, TEMPLATE, UPLOAD_COLUMNS)
    assert any("Unknown source column" in e.message for e in errors)


def test_concatenate_with_fewer_than_two_sources_is_not_blocking():
    """Arity is no longer enforced - a customer file might only have one of the source columns."""
    mappings = [
        MappingRule(destination="Customer ID", sources=["ID"], operation=Operation.COPY),
        MappingRule(destination="Customer Name", sources=["Name"], operation=Operation.COPY),
        MappingRule(destination="Address", sources=["Addr1"], operation=Operation.CONCATENATE),
    ]
    assert validate_mappings(mappings, TEMPLATE, UPLOAD_COLUMNS) == []


def test_copy_with_no_sources_is_not_blocking():
    """The auto-seeded default row for an unmatched destination has 0 sources - must not block."""
    mappings = [MappingRule(destination="Customer ID", sources=[], operation=Operation.COPY)]
    assert validate_mappings(mappings, TEMPLATE, UPLOAD_COLUMNS) == []


def test_constant_without_value_is_reported():
    mappings = [MappingRule(destination="Customer ID", sources=[], operation=Operation.CONSTANT)]
    errors = validate_mappings(mappings, TEMPLATE, UPLOAD_COLUMNS)
    assert any("options.value" in e.message for e in errors)


def test_duplicate_destination_is_reported():
    mappings = [
        MappingRule(destination="Customer ID", sources=["ID"], operation=Operation.COPY),
        MappingRule(destination="Customer ID", sources=["Name"], operation=Operation.COPY),
        MappingRule(destination="Customer Name", sources=["Name"], operation=Operation.COPY),
    ]
    errors = validate_mappings(mappings, TEMPLATE, UPLOAD_COLUMNS)
    assert any("Duplicate mapping" in e.message for e in errors)
