def test_accounting_status(client):
    response = client.get("/accounting/status")

    assert response.status_code == 200

    data = response.json()

    assert data["module"] == "accounting"
    assert data["status"] == "active"
    assert data["message"] == "Accounting module is running"


def test_accounting_module_is_loaded(client):
    response = client.get("/system/modules")

    assert response.status_code == 200

    modules = response.json()
    accounting_module = next(
        module for module in modules if module["name"] == "accounting"
    )

    assert accounting_module["enabled"] is True
    assert accounting_module["implemented"] is True
    assert accounting_module["loaded"] is True
    assert accounting_module["error"] is None