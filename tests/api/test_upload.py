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
