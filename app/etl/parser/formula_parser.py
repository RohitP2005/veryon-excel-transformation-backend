"""Safe evaluator for a curated, Excel-like formula language operating on `{{Column}}`
placeholders.

Never uses eval()/exec() on raw formula strings. Instead it substitutes each `{{Column}}`
placeholder with a generated variable name, parses the result with `ast.parse`, and walks the
resulting AST allowing only: numeric/text/boolean literals, the substituted variables, arithmetic
(+ - * / % ** and unary +/-), single comparisons (< <= > >= == != and Excel's <>), and a
whitelisted set of Excel-style functions (IF, ROUND, CONCATENATE, LEFT, ...). Anything else
(arbitrary function calls, attribute/subscript access, names that aren't a known placeholder,
etc.) raises FormulaError instead of being executed.

Deliberately NOT supported, because this evaluates one mapping row at a time rather than a full
spreadsheet: cell/range references (A1, B2:B10), cross-row aggregation (summing a column),
lookups (VLOOKUP/INDEX-MATCH), and date/time functions.

Known limitation: `^` and `<>` are translated to `**`/`!=` with a plain text substitution before
parsing, so a formula that needs a literal `^` or `<>` inside a quoted string (rare in practice)
would be mangled too.
"""
import ast
import math
import operator
import re
from collections.abc import Callable
from typing import Any

_PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")

# Function names that collide with Python keywords (if/and/or/not) - typed in lowercase, as
# Excel users naturally would, they'd otherwise be a SyntaxError before we ever see the AST.
_KEYWORD_LIKE_FUNCTIONS = re.compile(r"(?i)\b(if|and|or|not)\b(?=\s*\()")

# A bare "=" is how Excel spells equality (IF({{Qty}}=0, ...)), but left as-is it reads as
# Python's keyword-argument syntax inside a call and fails to parse - normalize it to "==",
# taking care not to touch an existing ==, !=, <=, or >=.
_SINGLE_EQUALS_PATTERN = re.compile(r"(?<![=!<>])=(?!=)")

_BINOPS: dict[type, Callable[[float, float], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARYOPS: dict[type, Callable[[float], float]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

_COMPARE_OPS: dict[type, Callable[[Any, Any], bool]] = {
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
}


class FormulaError(ValueError):
    """Raised when a formula references an unknown column or uses disallowed syntax."""


def extract_placeholders(formula: str) -> list[str]:
    """Return the (order-preserved, de-duplicated) `{{Column}}` names referenced in a formula."""
    return list(dict.fromkeys(m.strip() for m in _PLACEHOLDER_PATTERN.findall(formula)))


def _normalize_excel_syntax(expr: str) -> str:
    expr = expr.replace("<>", "!=").replace("^", "**")
    expr = _SINGLE_EQUALS_PATTERN.sub("==", expr)
    return _KEYWORD_LIKE_FUNCTIONS.sub(lambda m: m.group(1).upper(), expr)


def evaluate_formula(formula: str, row_values: dict[str, Any]) -> Any:
    var_names: dict[str, str] = {}

    def _replace(match: re.Match[str]) -> str:
        column = match.group(1).strip()
        if column not in row_values:
            raise FormulaError(f"Unknown column referenced in formula: '{column}'")
        var_name = f"__v{len(var_names)}__"
        var_names[var_name] = column
        return var_name

    expr = _PLACEHOLDER_PATTERN.sub(_replace, formula)
    expr = _normalize_excel_syntax(expr)

    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise FormulaError(f"Invalid formula syntax: {formula}") from exc

    return _eval_node(tree, var_names, row_values, formula)


def _to_number(value: Any, *, what: str = "value") -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise FormulaError(f"Expected a numeric {what}, got {value!r}") from exc


def _to_text(value: Any) -> str:
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _require_args(name: str, args: list[Any], minimum: int, maximum: int | None = None) -> None:
    maximum = minimum if maximum is None else maximum
    if not minimum <= len(args) <= maximum:
        span = f"exactly {minimum}" if minimum == maximum else f"{minimum}-{maximum}"
        raise FormulaError(f"{name}() requires {span} argument(s), got {len(args)}")


def _round_half_away_from_zero(value: float, digits: int) -> float:
    factor = 10**digits
    scaled = value * factor
    rounded = math.floor(scaled + 0.5) if scaled >= 0 else math.ceil(scaled - 0.5)
    return rounded / factor


def _round_toward(value: float, digits: int, *, away_from_zero: bool) -> float:
    factor = 10**digits
    scaled = value * factor
    if away_from_zero:
        rounded = math.ceil(scaled) if scaled >= 0 else math.floor(scaled)
    else:
        rounded = math.floor(scaled) if scaled >= 0 else math.ceil(scaled)
    return rounded / factor


def _fn_round(args: list[Any]) -> float:
    _require_args("ROUND", args, 2)
    return _round_half_away_from_zero(_to_number(args[0]), int(_to_number(args[1])))


def _fn_roundup(args: list[Any]) -> float:
    _require_args("ROUNDUP", args, 2)
    return _round_toward(_to_number(args[0]), int(_to_number(args[1])), away_from_zero=True)


def _fn_rounddown(args: list[Any]) -> float:
    _require_args("ROUNDDOWN", args, 2)
    return _round_toward(_to_number(args[0]), int(_to_number(args[1])), away_from_zero=False)


def _fn_abs(args: list[Any]) -> float:
    _require_args("ABS", args, 1)
    return abs(_to_number(args[0]))


def _fn_int(args: list[Any]) -> float:
    _require_args("INT", args, 1)
    return float(math.floor(_to_number(args[0])))


def _fn_trunc(args: list[Any]) -> float:
    _require_args("TRUNC", args, 1, 2)
    digits = int(_to_number(args[1])) if len(args) > 1 else 0
    factor = 10**digits
    return math.trunc(_to_number(args[0]) * factor) / factor


def _fn_sqrt(args: list[Any]) -> float:
    _require_args("SQRT", args, 1)
    value = _to_number(args[0])
    if value < 0:
        raise FormulaError("SQRT() argument must not be negative")
    return math.sqrt(value)


def _fn_power(args: list[Any]) -> float:
    _require_args("POWER", args, 2)
    return _to_number(args[0]) ** _to_number(args[1])


def _fn_mod(args: list[Any]) -> float:
    _require_args("MOD", args, 2)
    divisor = _to_number(args[1])
    if divisor == 0:
        raise FormulaError("MOD() divisor must not be zero")
    return _to_number(args[0]) % divisor


def _fn_min(args: list[Any]) -> float:
    if not args:
        raise FormulaError("MIN() requires at least 1 argument")
    return min(_to_number(a) for a in args)


def _fn_max(args: list[Any]) -> float:
    if not args:
        raise FormulaError("MAX() requires at least 1 argument")
    return max(_to_number(a) for a in args)


def _fn_sum(args: list[Any]) -> float:
    return sum(_to_number(a) for a in args)


def _fn_average(args: list[Any]) -> float:
    if not args:
        raise FormulaError("AVERAGE() requires at least 1 argument")
    return _fn_sum(args) / len(args)


def _fn_concatenate(args: list[Any]) -> str:
    return "".join(_to_text(a) for a in args)


def _fn_left(args: list[Any]) -> str:
    _require_args("LEFT", args, 1, 2)
    n = int(_to_number(args[1])) if len(args) > 1 else 1
    return _to_text(args[0])[: max(n, 0)]


def _fn_right(args: list[Any]) -> str:
    _require_args("RIGHT", args, 1, 2)
    n = int(_to_number(args[1])) if len(args) > 1 else 1
    text = _to_text(args[0])
    return text[-n:] if n > 0 else ""


def _fn_mid(args: list[Any]) -> str:
    _require_args("MID", args, 3)
    start = int(_to_number(args[1]))
    length = int(_to_number(args[2]))
    if start < 1:
        raise FormulaError("MID()'s start position must be 1 or greater")
    return _to_text(args[0])[start - 1 : start - 1 + max(length, 0)]


def _fn_len(args: list[Any]) -> int:
    _require_args("LEN", args, 1)
    return len(_to_text(args[0]))


def _fn_upper(args: list[Any]) -> str:
    _require_args("UPPER", args, 1)
    return _to_text(args[0]).upper()


def _fn_lower(args: list[Any]) -> str:
    _require_args("LOWER", args, 1)
    return _to_text(args[0]).lower()


def _fn_trim(args: list[Any]) -> str:
    _require_args("TRIM", args, 1)
    return " ".join(_to_text(args[0]).split())


def _fn_substitute(args: list[Any]) -> str:
    _require_args("SUBSTITUTE", args, 3, 4)
    text, old, new = _to_text(args[0]), _to_text(args[1]), _to_text(args[2])
    if len(args) < 4:
        return text.replace(old, new)
    instance = int(_to_number(args[3]))
    parts = text.split(old)
    if instance < 1 or instance >= len(parts):
        return text
    return old.join(parts[:instance]) + new + old.join(parts[instance:])


def _fn_and(args: list[Any]) -> bool:
    if not args:
        raise FormulaError("AND() requires at least 1 argument")
    return all(bool(a) for a in args)


def _fn_or(args: list[Any]) -> bool:
    if not args:
        raise FormulaError("OR() requires at least 1 argument")
    return any(bool(a) for a in args)


def _fn_not(args: list[Any]) -> bool:
    _require_args("NOT", args, 1)
    return not bool(args[0])


_EAGER_FUNCTIONS: dict[str, Callable[[list[Any]], Any]] = {
    "ROUND": _fn_round,
    "ROUNDUP": _fn_roundup,
    "ROUNDDOWN": _fn_rounddown,
    "ABS": _fn_abs,
    "INT": _fn_int,
    "TRUNC": _fn_trunc,
    "SQRT": _fn_sqrt,
    "POWER": _fn_power,
    "MOD": _fn_mod,
    "MIN": _fn_min,
    "MAX": _fn_max,
    "SUM": _fn_sum,
    "AVERAGE": _fn_average,
    "CONCATENATE": _fn_concatenate,
    "CONCAT": _fn_concatenate,
    "LEFT": _fn_left,
    "RIGHT": _fn_right,
    "MID": _fn_mid,
    "LEN": _fn_len,
    "UPPER": _fn_upper,
    "LOWER": _fn_lower,
    "TRIM": _fn_trim,
    "SUBSTITUTE": _fn_substitute,
    "AND": _fn_and,
    "OR": _fn_or,
    "NOT": _fn_not,
}


def _eval_node(node: ast.AST, var_names: dict[str, str], row_values: dict[str, Any], formula: str) -> Any:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body, var_names, row_values, formula)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float, bool, str)):
            return node.value
        raise FormulaError("Only numeric, text, or boolean literals are allowed in formulas")

    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        left = _to_number(_eval_node(node.left, var_names, row_values, formula), what="left operand")
        right = _to_number(_eval_node(node.right, var_names, row_values, formula), what="right operand")
        try:
            return _BINOPS[type(node.op)](left, right)
        except ZeroDivisionError as exc:
            raise FormulaError("Division by zero") from exc

    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARYOPS:
        operand = _to_number(_eval_node(node.operand, var_names, row_values, formula), what="operand")
        return _UNARYOPS[type(node.op)](operand)

    if isinstance(node, ast.Compare):
        if len(node.ops) != 1 or len(node.comparators) != 1 or type(node.ops[0]) not in _COMPARE_OPS:
            raise FormulaError(
                "Only a single comparison is supported per expression (e.g. {{A}} > {{B}}) - "
                "combine several with AND()/OR()"
            )
        left = _eval_node(node.left, var_names, row_values, formula)
        right = _eval_node(node.comparators[0], var_names, row_values, formula)
        try:
            return _COMPARE_OPS[type(node.ops[0])](left, right)
        except TypeError as exc:
            raise FormulaError(f"Cannot compare {left!r} and {right!r}") from exc

    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
        func_name = node.func.id.upper()

        if func_name == "IF":
            if len(node.args) != 3:
                raise FormulaError(
                    "IF() requires exactly 3 arguments: IF(condition, value_if_true, value_if_false)"
                )
            condition = _eval_node(node.args[0], var_names, row_values, formula)
            branch = node.args[1] if condition else node.args[2]
            return _eval_node(branch, var_names, row_values, formula)

        if func_name == "IFERROR":
            if len(node.args) != 2:
                raise FormulaError("IFERROR() requires exactly 2 arguments: IFERROR(value, value_if_error)")
            try:
                return _eval_node(node.args[0], var_names, row_values, formula)
            except FormulaError:
                return _eval_node(node.args[1], var_names, row_values, formula)

        if func_name in _EAGER_FUNCTIONS:
            args = [_eval_node(a, var_names, row_values, formula) for a in node.args]
            return _EAGER_FUNCTIONS[func_name](args)

        raise FormulaError(f"Unknown function '{func_name}' in formula: {formula}")

    if isinstance(node, ast.Name):
        upper = node.id.upper()
        if upper == "TRUE":
            return True
        if upper == "FALSE":
            return False
        if node.id in var_names:
            return row_values.get(var_names[node.id])

    raise FormulaError(f"Disallowed expression in formula: {formula}")


def validate_formula_syntax(formula: str) -> None:
    """Check that a formula is safe/well-formed before it's saved, without real row data.

    Substitutes every placeholder with a dummy numeric value and runs it through the same
    restricted evaluator used at generate time, so anything that would be rejected later
    (disallowed syntax, unknown functions, non-arithmetic expressions, etc.) is caught immediately.
    """
    placeholders = extract_placeholders(formula)
    dummy_values = dict.fromkeys(placeholders, 1.0)
    evaluate_formula(formula, dummy_values)
