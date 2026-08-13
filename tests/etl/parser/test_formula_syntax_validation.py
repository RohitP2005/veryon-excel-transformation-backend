import pytest

from app.etl.parser.formula_parser import FormulaError, validate_formula_syntax


def test_validate_formula_syntax_accepts_valid_arithmetic():
    validate_formula_syntax("{{Price}} * {{Quantity}}")
    validate_formula_syntax("({{Price}} + 5) / 2")


def test_validate_formula_syntax_rejects_function_calls():
    with pytest.raises(FormulaError):
        validate_formula_syntax("__import__('os').system('echo hi')")


def test_validate_formula_syntax_rejects_bad_syntax():
    with pytest.raises(FormulaError):
        validate_formula_syntax("{{Price}} *")
