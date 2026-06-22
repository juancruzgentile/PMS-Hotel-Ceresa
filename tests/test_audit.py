from ceresa.audit import repository as audit_repository
from ceresa.db import get_connection


def create_audit_test_reservation(client) -> tuple[int, int]:
    guest_response = client.post(
        "/guests",
        json={
            "guest_code": "AUDIT-GUEST-001",
            "first_name": "Audit",
            "last_name": "Guest",
            "email": None,
            "phone": None,
            "nationality": None,
            "notes": None,
        },
    )
    room_response = client.post(
        "/rooms",
        json={
            "room_number": "AUD-001",
            "floor": 1,
            "room_type": "Audit Test",
            "has_jacuzzi": False,
            "has_balcony": False,
            "notes": None,
        },
    )
    reservation_response = client.post(
        "/reservations",
        json={
            "reservation_code": "AUDIT-RES-001",
            "guest_id": guest_response.json()["guest_id"],
            "room_id": room_response.json()["room_id"],
            "check_in_date": "2027-05-01",
            "check_out_date": "2027-05-05",
            "status": "confirmed",
            "adults": 1,
            "children": 0,
            "notes": None,
        },
    )

    assert guest_response.status_code == 200
    assert room_response.status_code == 200
    assert reservation_response.status_code == 200

    return (
        reservation_response.json()["reservation_id"],
        room_response.json()["room_id"],
    )


def test_audit_repository_creates_lists_and_gets_event(
    client,
    reset_test_data,
):
    reservation_id, room_id = create_audit_test_reservation(client)

    with get_connection() as connection:
        event_id = audit_repository.create_audit_event_with_connection(
            connection,
            {
                "module": "reception",
                "event_type": "test_event",
                "entity_type": "reservation",
                "entity_id": reservation_id,
                "reservation_id": reservation_id,
                "room_id": room_id,
                "billing_account_id": None,
                "actor_user_id": None,
                "before_state_json": "{}",
                "after_state_json": "{}",
                "metadata_json": "{}",
            },
        )
        connection.commit()

    events = audit_repository.list_audit_events_by_reservation_id(
        reservation_id
    )
    event = audit_repository.get_audit_event_by_id(event_id)

    assert len(events) == 1
    assert events[0]["id"] == event_id
    assert event["event_type"] == "test_event"
    assert event["reservation_id"] == reservation_id
