"""Safe evaluator for `{{Column}} * {{Other}}` style formulas.

Never uses eval()/exec() on raw formula strings. Instead it substitutes each `{{Column}}`
placeholder with a generated variable name, parses the result with `ast.parse`, and walks the
resulting AST allowing only numeric literals, the substituted variables, and basic arithmetic
operators (+ - * / % ** and unary +/-). Anything else (function calls, attribute access, names
that aren't a known placeholder, etc.) raises FormulaError instead of being executed.
"""
import ast
import operator
import re
from typing import Any

_PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")

_BINOPS: dict[type, Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARYOPS: dict[type, Any] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


class FormulaError(ValueError):
    """Raised when a formula references an unknown column or uses disallowed syntax."""


def extract_placeholders(formula: str) -> list[str]:
    """Return the (order-preserved, de-duplicated) `{{Column}}` names referenced in a formula."""
    return list(dict.fromkeys(m.strip() for m in _PLACEHOLDER_PATTERN.findall(formula)))


def evaluate_formula(formula: str, row_values: dict[str, Any]) -> float:
    var_names: dict[str, str] = {}

    def _replace(match: re.Match[str]) -> str:
        column = match.group(1).strip()
        if column not in row_values:
            raise FormulaError(f"Unknown column referenced in formula: '{column}'")
        var_name = f"__v{len(var_names)}__"
        var_names[var_name] = column
        return var_name

    expr = _PLACEHOLDER_PATTERN.sub(_replace, formula)

    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise FormulaError(f"Invalid formula syntax: {formula}") from exc

    return _eval_node(tree, var_names, row_values, formula)


def _eval_node(node: ast.AST, var_names: dict[str, str], row_values: dict[str, Any], formula: str) -> float:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body, var_names, row_values, formula)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise FormulaError("Only numeric literals are allowed in formulas")
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        left = _eval_node(node.left, var_names, row_values, formula)
        right = _eval_node(node.right, var_names, row_values, formula)
        return _BINOPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARYOPS:
        return _UNARYOPS[type(node.op)](_eval_node(node.operand, var_names, row_values, formula))
    if isinstance(node, ast.Name) and node.id in var_names:
        column = var_names[node.id]
        value = row_values.get(column)
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise FormulaError(f"Column '{column}' value is not numeric: {value!r}") from exc
    raise FormulaError(f"Disallowed expression in formula: {formula}")
