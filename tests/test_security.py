def test_security_status(client):
    response = client.get("/security/status")

    assert response.status_code == 200

    data = response.json()

    assert data["module"] == "security"
    assert data["status"] == "active"
    assert data["message"] == "Security module is running"


def test_security_module_is_loaded(client):
    response = client.get("/system/modules")

    assert response.status_code == 200

    modules = response.json()
    security_module = next(
        module for module in modules if module["name"] == "security"
    )

    assert security_module["enabled"] is True
    assert security_module["implemented"] is True
    assert security_module["loaded"] is True
    assert security_module["error"] is None