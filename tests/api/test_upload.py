def test_upload_valid_excel_returns_columns_and_preview(client, customer_workbook_bytes):
    response = client.post(
        "/api/upload",
        files={
            "file": (
                "customers.xlsx",
                customer_workbook_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["columns"] == ["ID", "Name", "Mail", "Phone Number", "Addr1", "Addr2", "Nation"]
    assert body["row_count"] == 2
    assert len(body["sample_rows"]) == 2
    assert body["upload_id"]
    assert body["header_row"] == 1


def test_upload_with_header_row_offset(client, header_offset_workbook_bytes):
    """A title row before the real header must be skippable via the header_row field."""
    response = client.post(
        "/api/upload",
        data={"header_row": "2"},
        files={
            "file": (
                "fleet.xlsx",
                header_offset_workbook_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["columns"] == ["ID", "Name"]
    assert body["row_count"] == 2
    assert body["header_row"] == 2


def test_upload_rejects_invalid_header_row(client, customer_workbook_bytes):
    response = client.post(
        "/api/upload",
        data={"header_row": "0"},
        files={
            "file": (
                "customers.xlsx",
                customer_workbook_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 400


def test_upload_unmerges_merged_data_cells(client, merged_data_workbook_bytes):
    response = client.post(
        "/api/upload",
        files={
            "file": (
                "departments.xlsx",
                merged_data_workbook_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["sample_rows"][0]["Department"] == "Engineering"
    assert body["sample_rows"][1]["Department"] == "Engineering"


def test_upload_rejects_non_excel_extension(client):
    response = client.post("/api/upload", files={"file": ("notes.txt", b"hello", "text/plain")})
    assert response.status_code == 400


def test_upload_rejects_file_with_wrong_content(client):
    response = client.post(
        "/api/upload",
        files={
            "file": (
                "fake.xlsx",
                b"not a real workbook",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 400
