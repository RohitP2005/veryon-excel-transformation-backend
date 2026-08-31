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


def test_evaluate_formula_if_supports_excel_single_equals():
    assert evaluate_formula('IF({{Status}}="Closed", 1, 0)', {"Status": "Closed"}) == 1


def test_evaluate_formula_if_is_case_insensitive_and_lazy():
    """Lowercase "if" collides with the Python keyword unless normalized, and the untaken
    branch (division by zero) must never actually be evaluated."""
    assert evaluate_formula("if({{Qty}}=0, 0, {{Total}}/{{Qty}})", {"Qty": 0, "Total": 100}) == 0


def test_evaluate_formula_iferror_falls_back_on_division_by_zero():
    assert evaluate_formula("IFERROR({{Total}}/{{Qty}}, -1)", {"Qty": 0, "Total": 100}) == -1


def test_evaluate_formula_iferror_falls_back_on_unknown_function():
    assert evaluate_formula("IFERROR(NOPE(1), -1)", {}) == -1


def test_evaluate_formula_round_uses_half_away_from_zero():
    assert evaluate_formula("ROUND({{Value}}, 1)", {"Value": 2.25}) == 2.3
    assert evaluate_formula("ROUND({{Value}}, 1)", {"Value": -2.25}) == -2.3


def test_evaluate_formula_roundup_and_rounddown():
    assert evaluate_formula("ROUNDUP({{Value}}, 0)", {"Value": 2.1}) == 3
    assert evaluate_formula("ROUNDDOWN({{Value}}, 0)", {"Value": 2.9}) == 2


def test_evaluate_formula_text_functions():
    row = {"Name": "alice", "Status": "Closed"}
    assert evaluate_formula('CONCATENATE(UPPER({{Name}}), " - ", {{Status}})', row) == "ALICE - Closed"
    assert evaluate_formula("LEFT({{Status}}, 3)", row) == "Clo"
    assert evaluate_formula("RIGHT({{Status}}, 3)", row) == "sed"
    assert evaluate_formula("MID({{Status}}, 2, 3)", row) == "los"
    assert evaluate_formula("LEN({{Status}})", row) == 6
    assert evaluate_formula('SUBSTITUTE({{Status}}, "o", "0")', row) == "Cl0sed"
    assert evaluate_formula("TRIM({{Name}})", {"Name": "  alice  "}) == "alice"


def test_evaluate_formula_logical_functions_and_comparisons():
    row = {"Price": 10, "Quantity": 3}
    assert evaluate_formula("AND({{Price}} > 5, {{Quantity}} > 1)", row) is True
    assert evaluate_formula("OR({{Price}} > 50, {{Quantity}} > 1)", row) is True
    assert evaluate_formula("NOT({{Price}} > 50)", row) is True
    assert evaluate_formula("{{Price}} <> {{Quantity}}", row) is True
    assert evaluate_formula("TRUE", {}) is True
    assert evaluate_formula("false", {}) is False


def test_evaluate_formula_supports_math_functions():
    row = {"A": 10, "B": 3}
    assert evaluate_formula("MAX({{A}}, {{B}}, 100)", row) == 100
    assert evaluate_formula("MIN({{A}}, {{B}})", row) == 3
    assert evaluate_formula("SUM({{A}}, {{B}}, 1)", row) == 14
    assert evaluate_formula("MOD({{A}}, {{B}})", row) == 1
    assert evaluate_formula("2^10", {}) == 1024
    assert evaluate_formula("ABS(-5)", {}) == 5


def test_evaluate_formula_rejects_unknown_function():
    with pytest.raises(FormulaError):
        evaluate_formula("NOPE(1, 2)", {})


def test_evaluate_formula_rejects_chained_comparisons():
    with pytest.raises(FormulaError):
        evaluate_formula("1 < {{A}} < 10", {"A": 5})


def test_evaluate_formula_rejects_wrong_if_arg_count():
    with pytest.raises(FormulaError):
        evaluate_formula("IF({{A}} > 1, 2)", {"A": 5})
