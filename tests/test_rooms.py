def test_create_room(client, reset_test_data):
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


def test_list_rooms(client, reset_test_data):
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


def test_update_room_cleaning_status_to_dirty(client, reset_test_data):
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