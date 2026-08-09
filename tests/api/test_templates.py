def test_list_templates_returns_seeded_templates(client):
    response = client.get("/api/templates")
    assert response.status_code == 200
    ids = [t["id"] for t in response.json()]
    assert "customer_import" in ids
    assert "aircraft_parts" in ids


def test_get_template_detail(client):
    response = client.get("/api/templates/customer_import")
    assert response.status_code == 200
    body = response.json()
    assert body["columns"] == ["Customer ID", "Customer Name", "Email", "Phone", "Address", "Country"]
    assert body["required_columns"] == ["Customer ID", "Customer Name"]


def test_get_unknown_template_returns_404(client):
    response = client.get("/api/templates/does-not-exist")
    assert response.status_code == 404
