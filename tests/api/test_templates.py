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
