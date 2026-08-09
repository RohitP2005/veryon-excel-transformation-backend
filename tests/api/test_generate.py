def _upload(client, workbook_bytes, filename):
    response = client.post(
        "/api/upload",
        files={
            "file": (
                filename,
                workbook_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 200
    return response.json()["upload_id"]


def test_generate_customer_import_with_concatenate(client, customer_workbook_bytes):
    upload_id = _upload(client, customer_workbook_bytes, "customers.xlsx")

    payload = {
        "template_id": "customer_import",
        "upload_id": upload_id,
        "mappings": [
            {"destination": "Customer ID", "sources": ["ID"], "operation": "copy"},
            {"destination": "Customer Name", "sources": ["Name"], "operation": "copy"},
            {"destination": "Email", "sources": ["Mail"], "operation": "copy"},
            {"destination": "Phone", "sources": ["Phone Number"], "operation": "copy"},
            {
                "destination": "Address",
                "sources": ["Addr1", "Addr2"],
                "operation": "concatenate",
                "options": {"separator": ", "},
            },
            {"destination": "Country", "sources": ["Nation"], "operation": "copy"},
        ],
    }
    response = client.post("/api/generate", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/vnd.openxmlformats")
    assert "X-Job-Id" in response.headers


def test_generate_with_formula_operation(client, pricing_workbook_bytes):
    upload_id = _upload(client, pricing_workbook_bytes, "pricing.xlsx")

    payload = {
        "template_id": "inventory",
        "upload_id": upload_id,
        "mappings": [
            {"destination": "SKU", "sources": [], "operation": "constant", "options": {"value": "SKU-1"}},
            {"destination": "Product Name", "sources": [], "operation": "constant", "options": {"value": "Widget"}},
            {"destination": "Quantity", "sources": ["Quantity"], "operation": "copy"},
            {"destination": "Unit Price", "sources": ["Price"], "operation": "copy"},
            {
                "destination": "Total",
                "sources": ["Price", "Quantity"],
                "operation": "formula",
                "formula": "{{Price}} * {{Quantity}}",
            },
        ],
    }
    response = client.post("/api/generate", json=payload)
    assert response.status_code == 200


def test_generate_returns_400_for_invalid_mapping(client, customer_workbook_bytes):
    upload_id = _upload(client, customer_workbook_bytes, "customers.xlsx")

    payload = {
        "template_id": "customer_import",
        "upload_id": upload_id,
        "mappings": [{"destination": "Email", "sources": ["Mail"], "operation": "copy"}],
    }
    response = client.post("/api/generate", json=payload)
    assert response.status_code == 400
    body = response.json()
    assert body["detail"] == "Mapping validation failed"
    assert body["errors"]


def test_generate_returns_404_for_unknown_template(client, customer_workbook_bytes):
    upload_id = _upload(client, customer_workbook_bytes, "customers.xlsx")
    payload = {"template_id": "does-not-exist", "upload_id": upload_id, "mappings": []}
    response = client.post("/api/generate", json=payload)
    assert response.status_code == 404


def test_generate_returns_404_for_unknown_upload(client):
    payload = {"template_id": "customer_import", "upload_id": "does-not-exist", "mappings": []}
    response = client.post("/api/generate", json=payload)
    assert response.status_code == 404
