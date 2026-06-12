def test_transport_status(client):
    response = client.get("/transport/status")

    assert response.status_code == 200

    data = response.json()

    assert data["module"] == "transport"
    assert data["status"] == "active"
    assert data["message"] == "Transport module is running"


def test_transport_module_is_loaded(client):
    response = client.get("/system/modules")

    assert response.status_code == 200

    modules = response.json()
    transport_module = next(
        module for module in modules if module["name"] == "transport"
    )

    assert transport_module["enabled"] is True
    assert transport_module["implemented"] is True
    assert transport_module["loaded"] is True
    assert transport_module["error"] is None