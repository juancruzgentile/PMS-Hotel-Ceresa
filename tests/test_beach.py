def test_beach_status(client):
    response = client.get("/beach/status")

    assert response.status_code == 200

    data = response.json()

    assert data["module"] == "beach"
    assert data["status"] == "active"
    assert data["message"] == "Beach module is running"


def test_beach_module_is_loaded(client):
    response = client.get("/system/modules")

    assert response.status_code == 200

    modules = response.json()
    beach_module = next(
        module for module in modules if module["name"] == "beach"
    )

    assert beach_module["enabled"] is True
    assert beach_module["implemented"] is True
    assert beach_module["loaded"] is True
    assert beach_module["error"] is None