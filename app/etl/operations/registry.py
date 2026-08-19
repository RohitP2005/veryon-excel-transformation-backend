from app.etl.operations.append_text import AppendTextOperation
from app.etl.operations.base import BaseOperation
from app.etl.operations.concatenate import ConcatenateOperation
from app.etl.operations.constant import ConstantOperation
from app.etl.operations.copy import CopyOperation
from app.etl.operations.date_format import DateFormatOperation
from app.etl.operations.duration_format import DurationFormatOperation
from app.etl.operations.formula import FormulaOperation
from app.etl.operations.multiply import MultiplyOperation
from app.etl.operations.replace import ReplaceOperation
from app.etl.operations.text_case import LowercaseOperation, UppercaseOperation
from app.etl.operations.trim import TrimOperation
from app.schemas.mapping import Operation

_REGISTRY: dict[Operation, BaseOperation] = {
    Operation.COPY: CopyOperation(),
    Operation.TRIM: TrimOperation(),
    Operation.UPPERCASE: UppercaseOperation(),
    Operation.LOWERCASE: LowercaseOperation(),
    Operation.CONCATENATE: ConcatenateOperation(),
    Operation.MULTIPLY: MultiplyOperation(),
    Operation.FORMULA: FormulaOperation(),
    Operation.REPLACE: ReplaceOperation(),
    Operation.DATE_FORMAT: DateFormatOperation(),
    Operation.CONSTANT: ConstantOperation(),
    Operation.APPEND_TEXT: AppendTextOperation(),
    Operation.DURATION_FORMAT: DurationFormatOperation(),
}


def get_operation(operation: Operation) -> BaseOperation:
    """Resolve an Operation enum value to its executable instance.

    Adding a new transformation only requires a new Operation enum value, a class
    implementing BaseOperation, and one entry here — no existing code changes.
    """
    try:
        return _REGISTRY[operation]
    except KeyError as exc:
        raise ValueError(f"No operation registered for '{operation}'") from exc
