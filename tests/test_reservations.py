def test_reservations_status(client):
    response = client.get("/reservations/status")

    assert response.status_code == 200

    data = response.json()

    assert data["module"] == "reservations"
    assert data["status"] == "active"
    assert data["message"] == "Reservations module is running"


def test_reservations_module_is_loaded(client):
    response = client.get("/system/modules")

    assert response.status_code == 200

    modules = response.json()
    reservations_module = next(
        module for module in modules if module["name"] == "reservations"
    )

    assert reservations_module["enabled"] is True
    assert reservations_module["implemented"] is True
    assert reservations_module["loaded"] is True
    assert reservations_module["error"] is None

def create_test_guest(client, guest_code: str) -> int:
    response = client.post(
        "/guests",
        json={
            "guest_code": guest_code,
            "first_name": "Reservation",
            "last_name": "Guest",
            "email": None,
            "phone": None,
            "nationality": None,
            "notes": None,
        },
    )

    assert response.status_code == 200
    return response.json()["guest_id"]


def create_test_room(client, room_number: str) -> int:
    response = client.post(
        "/rooms",
        json={
            "room_number": room_number,
            "floor": 1,
            "room_type": "Reservation Test",
            "has_jacuzzi": False,
            "has_balcony": False,
            "notes": "Room created for reservation tests.",
        },
    )

    assert response.status_code == 200
    return response.json()["room_id"]


def test_create_reservation(client, reset_test_data):
    guest_id = create_test_guest(client, "TEST-GUEST-001")
    room_id = create_test_room(client, "TEST-RES-101")

    response = client.post(
        "/reservations",
        json={
            "reservation_code": "TEST-RESERVATION-001",
            "guest_id": guest_id,
            "room_id": room_id,
            "check_in_date": "2027-07-10",
            "check_out_date": "2027-07-15",
            "status": "confirmed",
            "adults": 2,
            "children": 0,
            "notes": "Reservation created by pytest.",
        },
    )

    assert response.status_code == 200
    assert (
        response.json()["message"]
        == "Reservation created successfully"
    )
    assert isinstance(
        response.json()["reservation_id"],
        int,
    )


def test_list_reservations(client, reset_test_data):
    guest_id = create_test_guest(client, "TEST-GUEST-002")
    room_id = create_test_room(client, "TEST-RES-102")

    client.post(
        "/reservations",
        json={
            "reservation_code": "TEST-RESERVATION-002",
            "guest_id": guest_id,
            "room_id": room_id,
            "check_in_date": "2027-08-01",
            "check_out_date": "2027-08-05",
            "status": "pending",
            "adults": 1,
            "children": 0,
            "notes": None,
        },
    )

    response = client.get("/reservations")

    assert response.status_code == 200

    reservation_codes = [
        reservation["reservation_code"]
        for reservation in response.json()
    ]

    assert "TEST-RESERVATION-002" in reservation_codes


def test_get_reservation_by_id(client, reset_test_data):
    guest_id = create_test_guest(client, "TEST-GUEST-003")
    room_id = create_test_room(client, "TEST-RES-103")

    create_response = client.post(
        "/reservations",
        json={
            "reservation_code": "TEST-RESERVATION-003",
            "guest_id": guest_id,
            "room_id": room_id,
            "check_in_date": "2027-09-01",
            "check_out_date": "2027-09-03",
            "status": "confirmed",
            "adults": 2,
            "children": 1,
            "notes": None,
        },
    )

    reservation_id = create_response.json()[
        "reservation_id"
    ]

    response = client.get(
        f"/reservations/{reservation_id}"
    )

    assert response.status_code == 200
    assert (
        response.json()["reservation_code"]
        == "TEST-RESERVATION-003"
    )
    assert response.json()["room_number"] == "TEST-RES-103"


def test_invalid_reservation_dates_are_rejected(
    client,
    reset_test_data,
):
    guest_id = create_test_guest(client, "TEST-GUEST-004")
    room_id = create_test_room(client, "TEST-RES-104")

    response = client.post(
        "/reservations",
        json={
            "reservation_code": "TEST-RESERVATION-004",
            "guest_id": guest_id,
            "room_id": room_id,
            "check_in_date": "2027-10-10",
            "check_out_date": "2027-10-10",
            "status": "pending",
            "adults": 1,
            "children": 0,
            "notes": None,
        },
    )

    assert response.status_code == 400


def test_overlapping_reservation_is_rejected(
    client,
    reset_test_data,
):
    guest_id = create_test_guest(client, "TEST-GUEST-005")
    room_id = create_test_room(client, "TEST-RES-105")

    first_response = client.post(
        "/reservations",
        json={
            "reservation_code": "TEST-RESERVATION-005-A",
            "guest_id": guest_id,
            "room_id": room_id,
            "check_in_date": "2027-11-10",
            "check_out_date": "2027-11-15",
            "status": "confirmed",
            "adults": 1,
            "children": 0,
            "notes": None,
        },
    )

    second_response = client.post(
        "/reservations",
        json={
            "reservation_code": "TEST-RESERVATION-005-B",
            "guest_id": guest_id,
            "room_id": room_id,
            "check_in_date": "2027-11-14",
            "check_out_date": "2027-11-18",
            "status": "pending",
            "adults": 1,
            "children": 0,
            "notes": None,
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409