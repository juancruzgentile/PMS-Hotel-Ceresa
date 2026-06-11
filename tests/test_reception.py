def test_reception_status(client):
    response = client.get("/reception/status")

    assert response.status_code == 200

    data = response.json()

    assert data["module"] == "reception"
    assert data["status"] == "active"
    assert data["message"] == "Reception module is running"


def test_reception_module_is_loaded(client):
    response = client.get("/system/modules")

    assert response.status_code == 200

    modules = response.json()
    reception_module = next(
        module for module in modules if module["name"] == "reception"
    )

    assert reception_module["enabled"] is True
    assert reception_module["implemented"] is True
    assert reception_module["loaded"] is True
    assert reception_module["error"] is None