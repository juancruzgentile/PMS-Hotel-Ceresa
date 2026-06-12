def test_reservations_status(client):
    response = client.get("/reservations/status")

    assert response.status_code == 200

    data = response.json()

    assert data["module"] == "reservations"
    assert data["status"] == "active"
    assert data["message"] == "Reservations module is running"


def test_reservations_module_is_loaded(client):
    response = client.get("/system/modules")

    assert response.status_code == 200

    modules = response.json()
    reservations_module = next(
        module for module in modules if module["name"] == "reservations"
    )

    assert reservations_module["enabled"] is True
    assert reservations_module["implemented"] is True
    assert reservations_module["loaded"] is True
    assert reservations_module["error"] is None