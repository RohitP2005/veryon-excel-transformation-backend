# Excel Transformation Tool — Backend

Python 3 / FastAPI implementation of the ETL backend described in
[docs/backend/SPECIFICATION.md](../docs/backend/SPECIFICATION.md).

## Requirements

- Python 3.11+

## Setup

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Run

```powershell
uvicorn app.main:app --reload
```

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- Health check: http://127.0.0.1:8000/health

See [docs/backend/API_REFERENCE.md](../docs/backend/API_REFERENCE.md) for full route documentation.

## Test

```powershell
pytest
```

```powershell
pytest --cov=app
```

## Project Layout

```
app/
├── api/            # FastAPI routers (health, templates, upload, generate, formulas)
├── services/       # etl_service.py — orchestrates the generate pipeline
├── etl/
│   ├── readers/     # Excel ingestion (pandas/openpyxl)
│   ├── writers/     # Excel generation (openpyxl)
│   ├── operations/  # One class per transformation + a registry
│   ├── parser/      # Safe formula placeholder substitution/evaluation
│   └── validators/  # Mapping business-rule validation
├── models/         # In-memory template registry, upload store, and saved-formula store (MVP, no DB yet)
├── schemas/        # Pydantic request/response models
├── templates/      # Built-in template definitions (JSON)
├── uploads/        # Uploaded files (gitignored contents)
├── output/         # Generated files (gitignored contents)
└── core/           # Settings, logging, domain exceptions
tests/
├── api/            # FastAPI TestClient integration tests
└── etl/            # Unit tests for operations, formula parser, validators
```

## Known MVP Limitations

- Only `.xlsx` is accepted (`.xls` requires the deprecated `xlrd` engine, and `.xlsm` is
  rejected to avoid macro execution risk).
- Template and upload state is kept in-process memory — restarting the server clears uploads
  (a database is a listed future-stack item).
- Saved formulas (the reusable-operation library) are persisted to a flat JSON file under the
  system temp dir — durable across restarts on a traditional host, but ephemeral per-instance
  on serverless deploys (same caveat as uploads/output; see `ETL_FORMULAS_FILE`).
- `/api/generate` runs synchronously; large files should eventually move to a background job
  (Celery, per the future stack).
