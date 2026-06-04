import os

os.environ["CERESA_DATABASE_PATH"] = "data/ceresa_test.db"

from fastapi.testclient import TestClient

from ceresa.main import app
from ceresa.db import initialize_database, get_connection


client = TestClient(app)


def reset_test_data() -> None:
    """
    Cleans test rooms before each test run.

    For now we are using the local SQLite database.
    Later we will move tests to a separate database.
    """
    initialize_database()

    with get_connection() as connection:
        connection.execute("DELETE FROM rooms WHERE room_number LIKE 'TEST-%'")
        connection.commit()


def test_health_check():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "app": "Ceresa PMS",
        "status": "running",
        "version": "0.1.0",
    }


def test_create_room():
    reset_test_data()

    payload = {
        "room_number": "TEST-101",
        "floor": 1,
        "room_type": "Deluxe Test",
        "has_jacuzzi": True,
        "has_balcony": False,
        "notes": "Test room created by pytest",
    }

    response = client.post("/rooms", json=payload)

    assert response.status_code == 200
    assert response.json()["message"] == "Room created successfully"
    assert isinstance(response.json()["room_id"], int)


def test_list_rooms():
    reset_test_data()

    payload = {
        "room_number": "TEST-102",
        "floor": 1,
        "room_type": "Standard Test",
        "has_jacuzzi": False,
        "has_balcony": False,
        "notes": "Room for list test",
    }

    client.post("/rooms", json=payload)

    response = client.get("/rooms")

    assert response.status_code == 200

    rooms = response.json()
    room_numbers = [room["room_number"] for room in rooms]

    assert "TEST-102" in room_numbers


def test_update_room_cleaning_status_to_dirty():
    reset_test_data()

    payload = {
        "room_number": "TEST-103",
        "floor": 2,
        "room_type": "Suite Test",
        "has_jacuzzi": True,
        "has_balcony": True,
        "notes": "Room for dirty status test",
    }

    create_response = client.post("/rooms", json=payload)
    room_id = create_response.json()["room_id"]

    update_response = client.patch(
        f"/rooms/{room_id}/status",
        json={"cleaning_status": "dirty"},
    )

    assert update_response.status_code == 200
    assert update_response.json() == {
        "message": "Room status updated successfully",
        "room_id": room_id,
    }

    get_response = client.get(f"/rooms/{room_id}")
    room = get_response.json()

    assert room["cleaning_status"] == "dirty"


def test_housekeeping_dirty_rooms():
    reset_test_data()

    payload = {
        "room_number": "TEST-104",
        "floor": 2,
        "room_type": "Deluxe Test",
        "has_jacuzzi": False,
        "has_balcony": True,
        "notes": "Room for housekeeping test",
    }

    create_response = client.post("/rooms", json=payload)
    room_id = create_response.json()["room_id"]

    client.patch(
        f"/rooms/{room_id}/status",
        json={"cleaning_status": "dirty"},
    )

    housekeeping_response = client.get("/housekeeping/dirty-rooms")

    assert housekeeping_response.status_code == 200

    dirty_rooms = housekeeping_response.json()
    dirty_room_numbers = [room["room_number"] for room in dirty_rooms]

    assert "TEST-104" in dirty_room_numbers


def test_clean_room_disappears_from_housekeeping():
    reset_test_data()

    payload = {
        "room_number": "TEST-105",
        "floor": 3,
        "room_type": "Standard Test",
        "has_jacuzzi": False,
        "has_balcony": False,
        "notes": "Room for clean housekeeping test",
    }

    create_response = client.post("/rooms", json=payload)
    room_id = create_response.json()["room_id"]

    client.patch(
        f"/rooms/{room_id}/status",
        json={"cleaning_status": "dirty"},
    )

    client.patch(
        f"/rooms/{room_id}/status",
        json={"cleaning_status": "clean"},
    )

    housekeeping_response = client.get("/housekeeping/dirty-rooms")

    assert housekeeping_response.status_code == 200

    dirty_rooms = housekeeping_response.json()
    dirty_room_numbers = [room["room_number"] for room in dirty_rooms]

    assert "TEST-105" not in dirty_room_numbers


def test_system_health():
    response = client.get("/system/health")

    assert response.status_code == 200
    assert response.json()["app"] == "Ceresa PMS"
    assert response.json()["status"] == "running"


def test_system_modules():
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


def test_maintenance_repair_rooms():
    reset_test_data()

    payload = {
        "room_number": "TEST-201",
        "floor": 2,
        "room_type": "Suite Maintenance Test",
        "has_jacuzzi": True,
        "has_balcony": True,
        "notes": "Room for maintenance test",
    }

    create_response = client.post("/rooms", json=payload)
    room_id = create_response.json()["room_id"]

    client.patch(
        f"/rooms/{room_id}/status",
        json={"maintenance_status": "needs_repair"},
    )

    maintenance_response = client.get("/maintenance/repair-rooms")

    assert maintenance_response.status_code == 200

    repair_rooms = maintenance_response.json()
    repair_room_numbers = [room["room_number"] for room in repair_rooms]

    assert "TEST-201" in repair_room_numbers

def test_room_can_be_marked_in_repair():
    reset_test_data()

    payload = {
        "room_number": "TEST-202",
        "floor": 2,
        "room_type": "Suite Repair Flow Test",
        "has_jacuzzi": True,
        "has_balcony": True,
        "notes": "Room for in_repair status test",
    }

    create_response = client.post("/rooms", json=payload)
    room_id = create_response.json()["room_id"]

    client.patch(
        f"/rooms/{room_id}/status",
        json={"maintenance_status": "needs_repair"},
    )

    update_response = client.patch(
        f"/rooms/{room_id}/status",
        json={"maintenance_status": "in_repair"},
    )

    assert update_response.status_code == 200

    get_response = client.get(f"/rooms/{room_id}")
    room = get_response.json()

    assert room["maintenance_status"] == "in_repair"  
def test_room_can_return_to_ok_after_repair():
    reset_test_data()

    payload = {
        "room_number": "TEST-203",
        "floor": 2,
        "room_type": "Suite Repair Complete Test",
        "has_jacuzzi": False,
        "has_balcony": True,
        "notes": "Room for completed repair test",
    }

    create_response = client.post("/rooms", json=payload)
    room_id = create_response.json()["room_id"]

    client.patch(
        f"/rooms/{room_id}/status",
        json={"maintenance_status": "needs_repair"},
    )

    client.patch(
        f"/rooms/{room_id}/status",
        json={"maintenance_status": "in_repair"},
    )

    final_response = client.patch(
        f"/rooms/{room_id}/status",
        json={"maintenance_status": "ok"},
    )

    assert final_response.status_code == 200

    get_response = client.get(f"/rooms/{room_id}")
    room = get_response.json()

    assert room["maintenance_status"] == "ok"
      