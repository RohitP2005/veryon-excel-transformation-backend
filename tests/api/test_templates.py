def test_list_templates_returns_seeded_templates(client):
    response = client.get("/api/templates")
    assert response.status_code == 200
    ids = [t["id"] for t in response.json()]
    assert "model_tree" in ids
    assert "maintenance_task" in ids


def test_get_template_detail(client):
    response = client.get("/api/templates/model_tree")
    assert response.status_code == 200
    body = response.json()
    assert body["columns"] == ["Model", "HigherModel", "Location", "Position"]
    assert body["required_columns"] == ["Model", "HigherModel"]


def test_get_unknown_template_returns_404(client):
    response = client.get("/api/templates/does-not-exist")
    assert response.status_code == 404


def test_create_template_from_uploaded_headers(client, customer_workbook_bytes):
    response = client.post(
        "/api/templates",
        data={"name": "My New Template", "description": "A custom template"},
        files={
            "file": (
                "sample.xlsx",
                customer_workbook_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == "my_new_template"
    assert body["name"] == "My New Template"
    assert body["description"] == "A custom template"
    assert body["sheet_name"] == "My New Template"
    assert body["columns"] == ["ID", "Name", "Mail", "Phone Number", "Addr1", "Addr2", "Nation"]
    assert body["required_columns"] == []


def test_created_template_appears_in_list_and_detail(client, customer_workbook_bytes):
    client.post(
        "/api/templates",
        data={"name": "Roster"},
        files={"file": ("sample.xlsx", customer_workbook_bytes, "application/octet-stream")},
    )

    listed = client.get("/api/templates").json()
    assert any(t["id"] == "roster" for t in listed)

    detail = client.get("/api/templates/roster")
    assert detail.status_code == 200
    assert detail.json()["columns"]


def test_create_template_deduplicates_slug(client, customer_workbook_bytes):
    for _ in range(2):
        response = client.post(
            "/api/templates",
            data={"name": "Duplicate Name"},
            files={"file": ("sample.xlsx", customer_workbook_bytes, "application/octet-stream")},
        )
        assert response.status_code == 201
    ids = [t["id"] for t in client.get("/api/templates").json() if t["name"] == "Duplicate Name"]
    assert sorted(ids) == ["duplicate_name", "duplicate_name_2"]


def test_create_template_requires_name(client, customer_workbook_bytes):
    response = client.post(
        "/api/templates",
        data={"name": "  "},
        files={"file": ("sample.xlsx", customer_workbook_bytes, "application/octet-stream")},
    )
    assert response.status_code == 422


def test_create_template_rejects_non_excel_file(client):
    response = client.post(
        "/api/templates",
        data={"name": "Bad File"},
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400


def test_create_template_respects_header_row_offset(client, header_offset_workbook_bytes):
    response = client.post(
        "/api/templates",
        data={"name": "Fleet Template", "header_row": "2"},
        files={"file": ("fleet.xlsx", header_offset_workbook_bytes, "application/octet-stream")},
    )
    assert response.status_code == 201
    assert response.json()["columns"] == ["ID", "Name"]
