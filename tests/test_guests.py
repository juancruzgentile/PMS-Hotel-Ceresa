def test_guests_status(client):
    response = client.get("/guests/status")

    assert response.status_code == 200

    data = response.json()

    assert data["module"] == "guests"
    assert data["status"] == "active"
    assert data["message"] == "Guests module is running"


def test_guests_module_is_loaded(client):
    response = client.get("/system/modules")

    assert response.status_code == 200

    modules = response.json()
    guests_module = next(
        module for module in modules if module["name"] == "guests"
    )

    assert guests_module["enabled"] is True
    assert guests_module["implemented"] is True
    assert guests_module["loaded"] is True
    assert guests_module["error"] is None