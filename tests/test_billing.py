def test_billing_status(client):
    response = client.get("/billing/status")

    assert response.status_code == 200

    data = response.json()

    assert data["module"] == "billing"
    assert data["status"] == "active"
    assert data["message"] == "Billing module is running"


def test_billing_module_is_loaded(client):
    response = client.get("/system/modules")

    assert response.status_code == 200

    modules = response.json()
    billing_module = next(
        module for module in modules if module["name"] == "billing"
    )

    assert billing_module["enabled"] is True
    assert billing_module["implemented"] is True
    assert billing_module["loaded"] is True
    assert billing_module["error"] is None