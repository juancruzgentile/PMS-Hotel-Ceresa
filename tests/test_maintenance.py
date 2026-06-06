def test_maintenance_repair_rooms(client, reset_test_data):
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


def test_room_can_be_marked_in_repair(client, reset_test_data):
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


def test_room_can_return_to_ok_after_repair(client, reset_test_data):
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