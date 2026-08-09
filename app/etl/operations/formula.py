from typing import Any

from app.core.exceptions import ETLOperationError
from app.etl.parser.formula_parser import evaluate_formula


class FormulaOperation:
    def execute(self, values: list[Any], *, options: dict[str, Any]) -> Any:
        formula = options.get("formula")
        if not formula:
            raise ETLOperationError("Formula operation requires a 'formula' string")
        row = options.get("row", {})
        return evaluate_formula(formula, row)
