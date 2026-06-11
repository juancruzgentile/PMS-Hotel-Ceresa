def test_bar_status(client):
    response = client.get("/bar/status")

    assert response.status_code == 200

    data = response.json()

    assert data["module"] == "bar"
    assert data["status"] == "active"
    assert data["message"] == "Bar module is running"


def test_bar_module_is_loaded(client):
    response = client.get("/system/modules")

    assert response.status_code == 200

    modules = response.json()
    bar_module = next(
        module for module in modules if module["name"] == "bar"
    )

    assert bar_module["enabled"] is True
    assert bar_module["implemented"] is True
    assert bar_module["loaded"] is True
    assert bar_module["error"] is None