import pytest

from app.etl.parser.formula_parser import FormulaError, evaluate_formula, extract_placeholders


def test_extract_placeholders_returns_column_names():
    assert extract_placeholders("{{Price}} * {{Quantity}}") == ["Price", "Quantity"]


def test_evaluate_formula_computes_arithmetic():
    assert evaluate_formula("{{Price}} * {{Quantity}}", {"Price": 10, "Quantity": 3}) == 30.0


def test_evaluate_formula_supports_parentheses_and_addition():
    result = evaluate_formula("({{Price}} + 5) * {{Quantity}}", {"Price": 10, "Quantity": 2})
    assert result == 30.0


def test_evaluate_formula_rejects_unknown_column():
    with pytest.raises(FormulaError):
        evaluate_formula("{{Prix}} * 2", {"Price": 10})


def test_evaluate_formula_rejects_function_calls():
    with pytest.raises(FormulaError):
        evaluate_formula("__import__('os').system('echo hi')", {})


def test_evaluate_formula_rejects_attribute_access():
    with pytest.raises(FormulaError):
        evaluate_formula("{{Price}}.__class__", {"Price": 10})


def test_evaluate_formula_rejects_non_numeric_column_value():
    with pytest.raises(FormulaError):
        evaluate_formula("{{Name}} * 2", {"Name": "Alice"})
