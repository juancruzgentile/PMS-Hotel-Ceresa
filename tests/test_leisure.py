def test_leisure_status(client):
    response = client.get("/leisure/status")

    assert response.status_code == 200

    data = response.json()

    assert data["module"] == "leisure"
    assert data["status"] == "active"
    assert data["message"] == "Leisure module is running"


def test_leisure_module_is_loaded(client):
    response = client.get("/system/modules")

    assert response.status_code == 200

    modules = response.json()
    leisure_module = next(
        module for module in modules if module["name"] == "leisure"
    )

    assert leisure_module["enabled"] is True
    assert leisure_module["implemented"] is True
    assert leisure_module["loaded"] is True
    assert leisure_module["error"] is None