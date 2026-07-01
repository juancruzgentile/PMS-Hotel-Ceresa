import json

from ceresa.db import get_connection


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


def create_test_reservation(
    client,
    suffix: str,
    guest_id: int,
    room_id: int,
    check_in_date: str = "2028-01-10",
    check_out_date: str = "2028-01-15",
    status: str = "confirmed",
) -> int:
    response = client.post(
        "/reservations",
        json={
            "reservation_code": f"TEST-RESERVATION-{suffix}",
            "guest_id": guest_id,
            "room_id": room_id,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "status": status,
            "adults": 1,
            "children": 0,
            "notes": None,
        },
    )

    assert response.status_code == 200
    return response.json()["reservation_id"]


def create_actor_user(client, suffix: str) -> int:
    response = client.post(
        "/users",
        json={
            "username": f"reservation-actor-{suffix}".lower(),
            "full_name": "Reservation Actor",
            "email": None,
            "user_type": "director",
            "department_id": None,
        },
    )

    assert response.status_code == 200
    return response.json()["user_id"]


def set_reservation_status(reservation_id: int, status: str) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE reservations
            SET status = ?
            WHERE id = ?
            """,
            (
                status,
                reservation_id,
            ),
        )
        connection.commit()


def get_reservation_state(reservation_id: int) -> dict:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                id,
                room_id,
                check_in_date,
                check_out_date,
                status,
                updated_at
            FROM reservations
            WHERE id = ?
            """,
            (reservation_id,),
        ).fetchone()

    return dict(row)


def list_audit_events(reservation_id: int) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                module,
                event_type,
                reservation_id,
                room_id,
                actor_user_id,
                before_state_json,
                after_state_json,
                metadata_json
            FROM audit_events
            WHERE reservation_id = ?
            ORDER BY id
            """,
            (reservation_id,),
        ).fetchall()

    return [dict(row) for row in rows]


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


def test_cancel_confirmed_reservation_creates_audit_event(
    client,
    reset_test_data,
):
    guest_id = create_test_guest(client, "TEST-GUEST-CAN-001")
    room_id = create_test_room(client, "TEST-RES-CAN-001")
    reservation_id = create_test_reservation(
        client,
        "CAN-001",
        guest_id,
        room_id,
    )
    actor_user_id = create_actor_user(client, "CAN-001")

    response = client.patch(
        f"/reservations/{reservation_id}/cancel",
        json={
            "reason": "Guest changed plans.",
            "actor_user_id": actor_user_id,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert get_reservation_state(reservation_id)["status"] == "cancelled"

    events = list_audit_events(reservation_id)
    assert len(events) == 1
    assert events[0]["module"] == "reservations"
    assert events[0]["event_type"] == "reservation_cancelled"
    assert events[0]["actor_user_id"] == actor_user_id
    assert json.loads(events[0]["before_state_json"])[
        "reservation_status"
    ] == "confirmed"
    assert json.loads(events[0]["after_state_json"])[
        "reservation_status"
    ] == "cancelled"
    assert json.loads(events[0]["metadata_json"]) == {
        "reason": "Guest changed plans."
    }


def test_cancel_reservation_returns_404_for_missing_reservation(
    client,
    reset_test_data,
):
    response = client.patch(
        "/reservations/999999/cancel",
        json={},
    )

    assert response.status_code == 404


def test_cancel_reservation_blocks_already_cancelled(
    client,
    reset_test_data,
):
    guest_id = create_test_guest(client, "TEST-GUEST-CAN-002")
    room_id = create_test_room(client, "TEST-RES-CAN-002")
    reservation_id = create_test_reservation(
        client,
        "CAN-002",
        guest_id,
        room_id,
    )

    first_response = client.patch(
        f"/reservations/{reservation_id}/cancel",
        json={},
    )
    second_response = client.patch(
        f"/reservations/{reservation_id}/cancel",
        json={},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409


def test_cancel_reservation_blocks_checked_out(
    client,
    reset_test_data,
):
    guest_id = create_test_guest(client, "TEST-GUEST-CAN-003")
    room_id = create_test_room(client, "TEST-RES-CAN-003")
    reservation_id = create_test_reservation(
        client,
        "CAN-003",
        guest_id,
        room_id,
    )
    set_reservation_status(reservation_id, "checked_out")

    response = client.patch(
        f"/reservations/{reservation_id}/cancel",
        json={},
    )

    assert response.status_code == 409
    assert get_reservation_state(reservation_id)["status"] == "checked_out"
    assert list_audit_events(reservation_id) == []


def test_update_reservation_dates_changes_valid_dates_and_audits(
    client,
    reset_test_data,
):
    guest_id = create_test_guest(client, "TEST-GUEST-DAT-001")
    room_id = create_test_room(client, "TEST-RES-DAT-001")
    reservation_id = create_test_reservation(
        client,
        "DAT-001",
        guest_id,
        room_id,
    )
    actor_user_id = create_actor_user(client, "DAT-001")

    response = client.patch(
        f"/reservations/{reservation_id}/dates",
        json={
            "check_in_date": "2028-02-01",
            "check_out_date": "2028-02-05",
            "actor_user_id": actor_user_id,
        },
    )

    assert response.status_code == 200
    reservation = get_reservation_state(reservation_id)
    assert reservation["check_in_date"] == "2028-02-01"
    assert reservation["check_out_date"] == "2028-02-05"

    events = list_audit_events(reservation_id)
    assert len(events) == 1
    assert events[0]["event_type"] == "reservation_dates_changed"
    assert events[0]["actor_user_id"] == actor_user_id
    assert json.loads(events[0]["before_state_json"])[
        "check_in_date"
    ] == "2028-01-10"
    assert json.loads(events[0]["after_state_json"])[
        "check_out_date"
    ] == "2028-02-05"


def test_update_reservation_dates_rejects_invalid_range(
    client,
    reset_test_data,
):
    guest_id = create_test_guest(client, "TEST-GUEST-DAT-002")
    room_id = create_test_room(client, "TEST-RES-DAT-002")
    reservation_id = create_test_reservation(
        client,
        "DAT-002",
        guest_id,
        room_id,
    )

    response = client.patch(
        f"/reservations/{reservation_id}/dates",
        json={
            "check_in_date": "2028-02-05",
            "check_out_date": "2028-02-05",
        },
    )

    assert response.status_code == 400


def test_update_reservation_dates_rejects_active_overlap(
    client,
    reset_test_data,
):
    guest_id = create_test_guest(client, "TEST-GUEST-DAT-003")
    room_id = create_test_room(client, "TEST-RES-DAT-003")
    reservation_id = create_test_reservation(
        client,
        "DAT-003-A",
        guest_id,
        room_id,
        "2028-03-01",
        "2028-03-05",
    )
    create_test_reservation(
        client,
        "DAT-003-B",
        guest_id,
        room_id,
        "2028-03-10",
        "2028-03-15",
        "pending",
    )

    response = client.patch(
        f"/reservations/{reservation_id}/dates",
        json={
            "check_in_date": "2028-03-12",
            "check_out_date": "2028-03-14",
        },
    )

    assert response.status_code == 409
    assert get_reservation_state(reservation_id)[
        "check_in_date"
    ] == "2028-03-01"


def test_update_reservation_dates_allows_same_reservation_overlap(
    client,
    reset_test_data,
):
    guest_id = create_test_guest(client, "TEST-GUEST-DAT-004")
    room_id = create_test_room(client, "TEST-RES-DAT-004")
    reservation_id = create_test_reservation(
        client,
        "DAT-004",
        guest_id,
        room_id,
        "2028-04-01",
        "2028-04-05",
    )

    response = client.patch(
        f"/reservations/{reservation_id}/dates",
        json={
            "check_in_date": "2028-04-02",
            "check_out_date": "2028-04-06",
        },
    )

    assert response.status_code == 200


def test_update_reservation_dates_ignores_cancelled_and_checked_out_overlap(
    client,
    reset_test_data,
):
    guest_id = create_test_guest(client, "TEST-GUEST-DAT-005")
    room_id = create_test_room(client, "TEST-RES-DAT-005")
    reservation_id = create_test_reservation(
        client,
        "DAT-005-A",
        guest_id,
        room_id,
        "2028-05-01",
        "2028-05-05",
    )
    cancelled_id = create_test_reservation(
        client,
        "DAT-005-B",
        guest_id,
        room_id,
        "2028-05-10",
        "2028-05-15",
    )
    checked_out_id = create_test_reservation(
        client,
        "DAT-005-C",
        guest_id,
        room_id,
        "2028-05-20",
        "2028-05-25",
    )
    set_reservation_status(cancelled_id, "cancelled")
    set_reservation_status(checked_out_id, "checked_out")

    response = client.patch(
        f"/reservations/{reservation_id}/dates",
        json={
            "check_in_date": "2028-05-12",
            "check_out_date": "2028-05-22",
        },
    )

    assert response.status_code == 200


def test_update_reservation_dates_blocks_closed_statuses(
    client,
    reset_test_data,
):
    guest_id = create_test_guest(client, "TEST-GUEST-DAT-006")
    room_id = create_test_room(client, "TEST-RES-DAT-006")
    cancelled_id = create_test_reservation(
        client,
        "DAT-006-A",
        guest_id,
        room_id,
        "2028-06-01",
        "2028-06-05",
    )
    checked_out_id = create_test_reservation(
        client,
        "DAT-006-B",
        guest_id,
        room_id,
        "2028-06-10",
        "2028-06-15",
    )
    set_reservation_status(cancelled_id, "cancelled")
    set_reservation_status(checked_out_id, "checked_out")

    cancelled_response = client.patch(
        f"/reservations/{cancelled_id}/dates",
        json={
            "check_in_date": "2028-06-02",
            "check_out_date": "2028-06-06",
        },
    )
    checked_out_response = client.patch(
        f"/reservations/{checked_out_id}/dates",
        json={
            "check_in_date": "2028-06-11",
            "check_out_date": "2028-06-16",
        },
    )

    assert cancelled_response.status_code == 409
    assert checked_out_response.status_code == 409


def test_update_reservation_room_changes_to_valid_room_and_audits(
    client,
    reset_test_data,
):
    guest_id = create_test_guest(client, "TEST-GUEST-ROM-001")
    old_room_id = create_test_room(client, "TEST-RES-ROM-001-A")
    new_room_id = create_test_room(client, "TEST-RES-ROM-001-B")
    reservation_id = create_test_reservation(
        client,
        "ROM-001",
        guest_id,
        old_room_id,
    )
    actor_user_id = create_actor_user(client, "ROM-001")

    response = client.patch(
        f"/reservations/{reservation_id}/room",
        json={
            "room_id": new_room_id,
            "actor_user_id": actor_user_id,
        },
    )

    assert response.status_code == 200
    assert get_reservation_state(reservation_id)["room_id"] == new_room_id

    events = list_audit_events(reservation_id)
    assert len(events) == 1
    assert events[0]["event_type"] == "reservation_room_changed"
    assert events[0]["room_id"] == new_room_id
    assert events[0]["actor_user_id"] == actor_user_id
    assert json.loads(events[0]["before_state_json"])[
        "room_id"
    ] == old_room_id
    assert json.loads(events[0]["after_state_json"])[
        "room_id"
    ] == new_room_id


def test_update_reservation_room_returns_404_for_missing_room(
    client,
    reset_test_data,
):
    guest_id = create_test_guest(client, "TEST-GUEST-ROM-002")
    room_id = create_test_room(client, "TEST-RES-ROM-002")
    reservation_id = create_test_reservation(
        client,
        "ROM-002",
        guest_id,
        room_id,
    )

    response = client.patch(
        f"/reservations/{reservation_id}/room",
        json={"room_id": 999999},
    )

    assert response.status_code == 404


def test_update_reservation_room_rejects_active_overlap(
    client,
    reset_test_data,
):
    guest_id = create_test_guest(client, "TEST-GUEST-ROM-003")
    old_room_id = create_test_room(client, "TEST-RES-ROM-003-A")
    new_room_id = create_test_room(client, "TEST-RES-ROM-003-B")
    reservation_id = create_test_reservation(
        client,
        "ROM-003-A",
        guest_id,
        old_room_id,
        "2028-07-01",
        "2028-07-05",
    )
    create_test_reservation(
        client,
        "ROM-003-B",
        guest_id,
        new_room_id,
        "2028-07-02",
        "2028-07-04",
    )

    response = client.patch(
        f"/reservations/{reservation_id}/room",
        json={"room_id": new_room_id},
    )

    assert response.status_code == 409
    assert get_reservation_state(reservation_id)["room_id"] == old_room_id


def test_update_reservation_room_allows_same_reservation_overlap(
    client,
    reset_test_data,
):
    guest_id = create_test_guest(client, "TEST-GUEST-ROM-004")
    room_id = create_test_room(client, "TEST-RES-ROM-004")
    reservation_id = create_test_reservation(
        client,
        "ROM-004",
        guest_id,
        room_id,
    )

    response = client.patch(
        f"/reservations/{reservation_id}/room",
        json={"room_id": room_id},
    )

    assert response.status_code == 200
    assert get_reservation_state(reservation_id)["room_id"] == room_id


def test_update_reservation_room_blocks_closed_statuses(
    client,
    reset_test_data,
):
    guest_id = create_test_guest(client, "TEST-GUEST-ROM-005")
    first_room_id = create_test_room(client, "TEST-RES-ROM-005-A")
    second_room_id = create_test_room(client, "TEST-RES-ROM-005-B")
    cancelled_id = create_test_reservation(
        client,
        "ROM-005-A",
        guest_id,
        first_room_id,
        "2028-08-01",
        "2028-08-05",
    )
    checked_out_id = create_test_reservation(
        client,
        "ROM-005-B",
        guest_id,
        first_room_id,
        "2028-08-10",
        "2028-08-15",
    )
    set_reservation_status(cancelled_id, "cancelled")
    set_reservation_status(checked_out_id, "checked_out")

    cancelled_response = client.patch(
        f"/reservations/{cancelled_id}/room",
        json={"room_id": second_room_id},
    )
    checked_out_response = client.patch(
        f"/reservations/{checked_out_id}/room",
        json={"room_id": second_room_id},
    )

    assert cancelled_response.status_code == 409
    assert checked_out_response.status_code == 409
