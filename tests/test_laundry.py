def test_laundry_status(client):
    response = client.get("/laundry/status")

    assert response.status_code == 200

    data = response.json()

    assert data["module"] == "laundry"
    assert data["status"] == "active"
    assert data["message"] == "Laundry module is running"


def test_laundry_module_is_loaded(client):
    response = client.get("/system/modules")

    assert response.status_code == 200

    modules = response.json()
    laundry_module = next(
        module for module in modules if module["name"] == "laundry"
    )

    assert laundry_module["enabled"] is True
    assert laundry_module["implemented"] is True
    assert laundry_module["loaded"] is True
    assert laundry_module["error"] is None