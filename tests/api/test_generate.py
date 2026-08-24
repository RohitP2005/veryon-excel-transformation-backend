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


def test_generate_model_tree_with_concatenate(client, customer_workbook_bytes):
    upload_id = _upload(client, customer_workbook_bytes, "customers.xlsx")

    payload = {
        "template_id": "model_tree",
        "upload_id": upload_id,
        "mappings": [
            {"destination": "Model", "sources": ["ID"], "operation": "copy"},
            {"destination": "HigherModel", "sources": ["Name"], "operation": "copy"},
            {
                "destination": "Location",
                "sources": ["Addr1", "Addr2"],
                "operation": "concatenate",
                "options": {"separator": ", "},
            },
        ],
    }
    response = client.post("/api/generate", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/vnd.openxmlformats")
    assert "X-Job-Id" in response.headers


def test_generate_with_formula_operation(client, pricing_workbook_bytes):
    upload_id = _upload(client, pricing_workbook_bytes, "pricing.xlsx")

    payload = {
        "template_id": "model_tree",
        "upload_id": upload_id,
        "mappings": [
            {"destination": "Model", "sources": [], "operation": "constant", "options": {"value": "M-1"}},
            {"destination": "HigherModel", "sources": [], "operation": "constant", "options": {"value": "H-1"}},
            {
                "destination": "Position",
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
        "template_id": "model_tree",
        "upload_id": upload_id,
        "mappings": [{"destination": "Location", "sources": ["DoesNotExist"], "operation": "copy"}],
    }
    response = client.post("/api/generate", json=payload)
    assert response.status_code == 400
    body = response.json()
    assert body["detail"] == "Mapping validation failed"
    assert body["errors"]


def test_generate_leaves_unmapped_required_column_blank_instead_of_blocking(client, customer_workbook_bytes):
    """A required column (Model/HigherModel) with no matching customer column must not block
    generation - it should just come through blank in the output."""
    upload_id = _upload(client, customer_workbook_bytes, "customers.xlsx")

    payload = {
        "template_id": "model_tree",
        "upload_id": upload_id,
        "mappings": [{"destination": "Location", "sources": ["Addr1"], "operation": "copy"}],
    }
    response = client.post("/api/generate", json=payload)
    assert response.status_code == 200


def test_generate_appends_prefix_suffix_and_formats_duration(client, customer_workbook_bytes):
    upload_id = _upload(client, customer_workbook_bytes, "customers.xlsx")

    payload = {
        "template_id": "model_tree",
        "upload_id": upload_id,
        "mappings": [
            {"destination": "Model", "sources": [], "operation": "constant", "options": {"value": "M-1"}},
            {"destination": "HigherModel", "sources": [], "operation": "constant", "options": {"value": "H-1"}},
            {
                "destination": "Location",
                "sources": ["ID", "Name"],
                "operation": "concatenate",
                "options": {
                    "separator": ", ",
                    "formats": [{"duration_format": True, "suffix": " FH"}, {"suffix": " FC"}],
                },
            },
        ],
    }
    response = client.post("/api/generate", json=payload)
    assert response.status_code == 200


def test_generate_with_duration_pair_merge_operation(client, pricing_workbook_bytes):
    """Mirrors the TSN/CSN example: extract+format the first value, suffix both, merge."""
    upload_id = _upload(client, pricing_workbook_bytes, "pricing.xlsx")

    payload = {
        "template_id": "model_tree",
        "upload_id": upload_id,
        "mappings": [
            {"destination": "Model", "sources": [], "operation": "constant", "options": {"value": "M-1"}},
            {"destination": "HigherModel", "sources": [], "operation": "constant", "options": {"value": "H-1"}},
            {
                "destination": "Position",
                "sources": ["Price", "Quantity"],
                "operation": "duration_pair_merge",
            },
        ],
    }
    response = client.post("/api/generate", json=payload)
    assert response.status_code == 200


def test_generate_uses_combined_higher_order_header_column(client, multi_level_header_workbook_bytes):
    """Columns produced by a header_row_start range (e.g. "Engine 1 -> TSN") must be usable as
    mapping sources at generate time, proving the same range is applied to the full read."""
    response = client.post(
        "/api/upload",
        data={"header_row": "2", "header_row_start": "1"},
        files={
            "file": (
                "engines.xlsx",
                multi_level_header_workbook_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 200
    upload_id = response.json()["upload_id"]

    payload = {
        "template_id": "model_tree",
        "upload_id": upload_id,
        "mappings": [
            {"destination": "Model", "sources": [], "operation": "constant", "options": {"value": "M-1"}},
            {"destination": "HigherModel", "sources": [], "operation": "constant", "options": {"value": "H-1"}},
            {"destination": "Position", "sources": ["Engine 1 -> TSN"], "operation": "copy"},
        ],
    }
    response = client.post("/api/generate", json=payload)
    assert response.status_code == 200


def test_generate_returns_404_for_unknown_template(client, customer_workbook_bytes):
    upload_id = _upload(client, customer_workbook_bytes, "customers.xlsx")
    payload = {"template_id": "does-not-exist", "upload_id": upload_id, "mappings": []}
    response = client.post("/api/generate", json=payload)
    assert response.status_code == 404


def test_generate_returns_404_for_unknown_upload(client):
    payload = {"template_id": "model_tree", "upload_id": "does-not-exist", "mappings": []}
    response = client.post("/api/generate", json=payload)
    assert response.status_code == 404
