def test_kitchen_status(client):
    response = client.get("/kitchen/status")

    assert response.status_code == 200

    data = response.json()

    assert data["module"] == "kitchen"
    assert data["status"] == "active"
    assert data["message"] == "Kitchen module is running"


def test_kitchen_module_is_loaded(client):
    response = client.get("/system/modules")

    assert response.status_code == 200

    modules = response.json()
    kitchen_module = next(
        module for module in modules if module["name"] == "kitchen"
    )

    assert kitchen_module["enabled"] is True
    assert kitchen_module["implemented"] is True
    assert kitchen_module["loaded"] is True
    assert kitchen_module["error"] is None