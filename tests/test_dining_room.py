def test_dining_room_status(client):
    response = client.get("/dining-room/status")

    assert response.status_code == 200

    data = response.json()

    assert data["module"] == "dining_room"
    assert data["status"] == "active"
    assert data["message"] == "Dining room module is running"


def test_dining_room_module_is_loaded(client):
    response = client.get("/system/modules")

    assert response.status_code == 200

    modules = response.json()
    dining_room_module = next(
        module for module in modules if module["name"] == "dining_room"
    )

    assert dining_room_module["enabled"] is True
    assert dining_room_module["implemented"] is True
    assert dining_room_module["loaded"] is True
    assert dining_room_module["error"] is None