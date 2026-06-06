def test_housekeeping_dirty_rooms(client, reset_test_data):
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


def test_clean_room_disappears_from_housekeeping(client, reset_test_data):
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