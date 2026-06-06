def test_health_check(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "app": "Ceresa PMS",
        "status": "running",
        "version": "0.1.0",
    }


def test_system_health(client):
    response = client.get("/system/health")

    assert response.status_code == 200
    assert response.json()["app"] == "Ceresa PMS"
    assert response.json()["status"] == "running"


def test_system_modules(client):
    response = client.get("/system/modules")

    assert response.status_code == 200

    modules = response.json()
    module_names = [module["name"] for module in modules]

    assert "rooms" in module_names
    assert "housekeeping" in module_names
    assert "maintenance" in module_names
    assert "kitchen" in module_names
    assert "sala" in module_names
    assert "transport" in module_names

    rooms_module = next(module for module in modules if module["name"] == "rooms")
    housekeeping_module = next(
        module for module in modules if module["name"] == "housekeeping"
    )
    maintenance_module = next(
        module for module in modules if module["name"] == "maintenance"
    )

    assert rooms_module["enabled"] is True
    assert rooms_module["implemented"] is True
    assert rooms_module["loaded"] is True
    assert rooms_module["error"] is None

    assert housekeeping_module["enabled"] is True
    assert housekeeping_module["implemented"] is True
    assert housekeeping_module["loaded"] is True
    assert housekeeping_module["error"] is None

    assert maintenance_module["enabled"] is True
    assert maintenance_module["implemented"] is True
    assert maintenance_module["loaded"] is True
    assert maintenance_module["error"] is None


def test_system_hotel_config(client):
    response = client.get("/system/hotel")

    assert response.status_code == 200

    hotel_config = response.json()

    assert "hotel_name" in hotel_config
    assert "timezone" in hotel_config
    assert "currency" in hotel_config
    assert "default_language" in hotel_config
    assert "has_restaurant" in hotel_config
    assert "has_transport" in hotel_config