from app.etl.operations.concatenate import ConcatenateOperation
from app.etl.operations.constant import ConstantOperation
from app.etl.operations.copy import CopyOperation
from app.etl.operations.date_format import DateFormatOperation
from app.etl.operations.multiply import MultiplyOperation
from app.etl.operations.replace import ReplaceOperation
from app.etl.operations.text_case import LowercaseOperation, UppercaseOperation
from app.etl.operations.trim import TrimOperation


def test_copy_operation_returns_first_value():
    assert CopyOperation().execute(["hello"], options={}) == "hello"


def test_trim_operation_strips_whitespace():
    assert TrimOperation().execute(["  hi  "], options={}) == "hi"


def test_uppercase_and_lowercase():
    assert UppercaseOperation().execute(["abc"], options={}) == "ABC"
    assert LowercaseOperation().execute(["ABC"], options={}) == "abc"


def test_concatenate_joins_non_empty_values_with_separator():
    result = ConcatenateOperation().execute(["1 Main St", "", "Suite 5"], options={"separator": ", "})
    assert result == "1 Main St, Suite 5"


def test_concatenate_default_separator_is_space():
    assert ConcatenateOperation().execute(["Foo", "Bar"], options={}) == "Foo Bar"


def test_multiply_operation_computes_product():
    assert MultiplyOperation().execute([10, 3], options={}) == 30.0


def test_replace_operation_substitutes_text():
    result = ReplaceOperation().execute(["hello world"], options={"find": "world", "replace": "there"})
    assert result == "hello there"


def test_date_format_operation_formats_iso_string():
    result = DateFormatOperation().execute(["2026-01-05T00:00:00"], options={"format": "%d/%m/%Y"})
    assert result == "05/01/2026"


def test_constant_operation_returns_configured_value():
    assert ConstantOperation().execute([], options={"value": "N/A"}) == "N/A"
