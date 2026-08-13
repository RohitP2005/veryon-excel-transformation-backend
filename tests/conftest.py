import io

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook

from app.main import app
from app.models.formula_store import formula_store


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def _reset_formula_store():
    """The formula store is a real file on disk (module-level singleton) - keep tests isolated."""
    formula_store._write([])
    yield
    formula_store._write([])


def _build_workbook(headers: list[str], rows: list[list]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


@pytest.fixture()
def customer_workbook_bytes() -> bytes:
    return _build_workbook(
        headers=["ID", "Name", "Mail", "Phone Number", "Addr1", "Addr2", "Nation"],
        rows=[
            [1, "Alice", "alice@example.com", "555-1000", "1 Main St", "Suite 5", "USA"],
            [2, "Bob", "bob@example.com", "555-2000", "2 Oak Ave", "", "Canada"],
        ],
    )


@pytest.fixture()
def pricing_workbook_bytes() -> bytes:
    return _build_workbook(headers=["Price", "Quantity"], rows=[[10.0, 3], [5.5, 2]])
