from fastapi import APIRouter, HTTPException

from app.core.exceptions import SavedFormulaNotFoundError
from app.etl.parser.formula_parser import FormulaError, validate_formula_syntax
from app.models.formula_store import formula_store
from app.schemas.formula import SavedFormula, SavedFormulaCreate

router = APIRouter(prefix="/api/formulas", tags=["formulas"])


@router.get("", response_model=list[SavedFormula])
def list_formulas() -> list[SavedFormula]:
    return formula_store.list()


@router.post("", response_model=SavedFormula, status_code=201)
def create_formula(payload: SavedFormulaCreate) -> SavedFormula:
    try:
        validate_formula_syntax(payload.formula)
    except FormulaError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return formula_store.create(payload.name, payload.formula, payload.description)


@router.delete("/{formula_id}", status_code=204)
def delete_formula(formula_id: str) -> None:
    if not formula_store.delete(formula_id):
        raise SavedFormulaNotFoundError(formula_id)
