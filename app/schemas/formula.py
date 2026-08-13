from pydantic import BaseModel, Field


class SavedFormulaCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    formula: str = Field(min_length=1)
    description: str | None = None


class SavedFormula(SavedFormulaCreate):
    id: str
