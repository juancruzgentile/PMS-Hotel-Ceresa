def test_tourism_status(client):
    response = client.get("/tourism/status")

    assert response.status_code == 200

    data = response.json()

    assert data["module"] == "tourism"
    assert data["status"] == "active"
    assert data["message"] == "Tourism module is running"


def test_tourism_module_is_loaded(client):
    response = client.get("/system/modules")

    assert response.status_code == 200

    modules = response.json()
    tourism_module = next(
        module for module in modules if module["name"] == "tourism"
    )

    assert tourism_module["enabled"] is True
    assert tourism_module["implemented"] is True
    assert tourism_module["loaded"] is True
    assert tourism_module["error"] is None