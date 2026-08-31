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
    assert body["grid_columns"][:7] == ["A", "B", "C", "D", "E", "F", "G"]
    assert body["grid_rows"][0] == ["ID", "Name", "Mail", "Phone Number", "Addr1", "Addr2", "Nation"]
    assert body["grid_rows"][1][0] == 1


def test_upload_grid_ignores_header_row_offset(client, header_offset_workbook_bytes):
    """The raw grid must show the WHOLE sheet regardless of header_row - including the title
    row above the real headers - so the cell picker can select any value in the sheet."""
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
    assert body["columns"] == ["ID", "Name"]  # parsed view still respects header_row
    assert body["grid_rows"][0][0] == "Fleet Report - Confidential"  # raw grid does not
    assert body["grid_rows"][1] == ["ID", "Name"]


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


def test_upload_combines_higher_order_header_range(client, multi_level_header_workbook_bytes):
    """A header_row_start below header_row treats every row in between as a higher-order group
    header, forward-filled and chained onto the real field name."""
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
    body = response.json()
    assert body["columns"] == [
        "Engine 1 -> TSN",
        "Engine 1 -> TSO",
        "Engine 2 -> TSN",
        "Engine 2 -> TSO",
    ]
    assert body["row_count"] == 2
    assert body["sample_rows"][0]["Engine 1 -> TSN"] == 12530
    assert body["header_row"] == 2
    assert body["header_row_start"] == 1


def test_upload_combines_header_range_recursively_for_three_levels(
    client, three_level_header_workbook_bytes
):
    response = client.post(
        "/api/upload",
        data={"header_row": "3", "header_row_start": "1"},
        files={
            "file": (
                "aircraft.xlsx",
                three_level_header_workbook_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["columns"] == [
        "Aircraft -> Engine 1 -> TSN",
        "Aircraft -> Engine 1 -> TSO",
        "Aircraft -> Engine 2 -> TSN",
        "Aircraft -> Engine 2 -> TSO",
    ]


def test_upload_rejects_header_row_start_after_header_row(client, multi_level_header_workbook_bytes):
    response = client.post(
        "/api/upload",
        data={"header_row": "2", "header_row_start": "3"},
        files={
            "file": (
                "engines.xlsx",
                multi_level_header_workbook_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 400


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


def test_upload_dedupes_header_cell_merged_across_columns(client, merged_header_workbook_bytes):
    """A header merged across two columns (e.g. "TSA" spanning J:K) must surface as a single
    column, not one duplicate per cell the merge covers."""
    response = client.post(
        "/api/upload",
        files={
            "file": (
                "tsa.xlsx",
                merged_header_workbook_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["columns"] == ["ID", "TSA"]
    assert body["sample_rows"][0] == {"ID": 1, "TSA": 12530}
    assert body["sample_rows"][1] == {"ID": 2, "TSA": 13000}


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
