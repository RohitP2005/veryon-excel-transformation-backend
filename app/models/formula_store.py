"""File-backed store of user-saved reusable formulas (MVP: flat JSON file, no DB yet)."""
import json
import uuid
from pathlib import Path

from app.core.config import settings
from app.schemas.formula import SavedFormula


class SavedFormulaStore:
    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._file_path.exists():
            self._write([])

    def _read(self) -> list[SavedFormula]:
        raw = self._file_path.read_text(encoding="utf-8").strip()
        return [SavedFormula(**item) for item in (json.loads(raw) if raw else [])]

    def _write(self, formulas: list[SavedFormula]) -> None:
        payload = json.dumps([f.model_dump() for f in formulas], indent=2)
        self._file_path.write_text(payload, encoding="utf-8")

    def list(self) -> list[SavedFormula]:
        return self._read()

    def create(self, name: str, formula: str, description: str | None) -> SavedFormula:
        formulas = self._read()
        saved = SavedFormula(id=str(uuid.uuid4()), name=name, formula=formula, description=description)
        formulas.append(saved)
        self._write(formulas)
        return saved

    def delete(self, formula_id: str) -> bool:
        formulas = self._read()
        remaining = [f for f in formulas if f.id != formula_id]
        if len(remaining) == len(formulas):
            return False
        self._write(remaining)
        return True


formula_store = SavedFormulaStore(settings.formulas_file)
