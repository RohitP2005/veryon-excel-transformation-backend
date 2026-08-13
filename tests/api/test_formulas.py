def test_create_and_list_formula(client):
    response = client.post(
        "/api/formulas",
        json={"name": "Total Price", "formula": "{{Price}} * {{Quantity}}", "description": "Line total"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Total Price"
    assert body["formula"] == "{{Price}} * {{Quantity}}"
    assert body["id"]

    listed = client.get("/api/formulas").json()
    assert len(listed) == 1
    assert listed[0]["id"] == body["id"]


def test_create_formula_rejects_invalid_syntax(client):
    response = client.post("/api/formulas", json={"name": "Bad", "formula": "__import__('os')"})
    assert response.status_code == 400


def test_create_formula_rejects_empty_formula(client):
    response = client.post("/api/formulas", json={"name": "Empty", "formula": ""})
    assert response.status_code == 422


def test_delete_formula(client):
    created = client.post("/api/formulas", json={"name": "Discount", "formula": "{{Price}} * 0.9"}).json()

    response = client.delete(f"/api/formulas/{created['id']}")
    assert response.status_code == 204
    assert client.get("/api/formulas").json() == []


def test_delete_unknown_formula_returns_404(client):
    response = client.delete("/api/formulas/does-not-exist")
    assert response.status_code == 404
