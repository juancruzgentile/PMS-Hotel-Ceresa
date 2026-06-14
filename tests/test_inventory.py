def test_inventory_status(client):
    response = client.get("/inventory/status")

    assert response.status_code == 200

    data = response.json()

    assert data["module"] == "inventory"
    assert data["status"] == "active"
    assert data["message"] == "Inventory module is running"


def test_inventory_module_is_loaded(client):
    response = client.get("/system/modules")

    assert response.status_code == 200

    modules = response.json()
    inventory_module = next(
        module for module in modules if module["name"] == "inventory"
    )

    assert inventory_module["enabled"] is True
    assert inventory_module["implemented"] is True
    assert inventory_module["loaded"] is True
    assert inventory_module["error"] is None