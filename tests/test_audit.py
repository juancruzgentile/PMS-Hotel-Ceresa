from ceresa.audit import repository as audit_repository
from ceresa.db import get_connection


def create_audit_test_reservation(
    client,
    suffix: str = "001",
) -> tuple[int, int]:
    guest_response = client.post(
        "/guests",
        json={
            "guest_code": f"AUDIT-GUEST-{suffix}",
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
            "room_number": f"AUD-{suffix}",
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
            "reservation_code": f"AUDIT-RES-{suffix}",
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


def create_audit_test_event(
    client,
    suffix: str,
    module: str = "reception",
    event_type: str = "test_event",
) -> tuple[int, int, int]:
    reservation_id, room_id = create_audit_test_reservation(
        client,
        suffix,
    )

    with get_connection() as connection:
        event_id = audit_repository.create_audit_event_with_connection(
            connection,
            {
                "module": module,
                "event_type": event_type,
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

    return event_id, reservation_id, room_id


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


def test_audit_events_endpoint_returns_existing_events(
    client,
    reset_test_data,
):
    event_id, reservation_id, room_id = create_audit_test_event(
        client,
        "API-001",
    )

    response = client.get("/audit/events")

    assert response.status_code == 200

    events = response.json()
    event = next(item for item in events if item["id"] == event_id)

    assert event["reservation_id"] == reservation_id
    assert event["room_id"] == room_id
    assert event["module"] == "reception"
    assert event["event_type"] == "test_event"
    assert event["before_state"] == {}
    assert event["after_state"] == {}
    assert event["metadata"] == {}


def test_audit_events_endpoint_filters_by_reservation_id(
    client,
    reset_test_data,
):
    first_event_id, first_reservation_id, _ = create_audit_test_event(
        client,
        "API-002",
    )
    second_event_id, _, _ = create_audit_test_event(
        client,
        "API-003",
    )

    response = client.get(
        "/audit/events",
        params={"reservation_id": first_reservation_id},
    )

    assert response.status_code == 200

    event_ids = [event["id"] for event in response.json()]

    assert first_event_id in event_ids
    assert second_event_id not in event_ids


def test_audit_events_endpoint_filters_by_module_and_event_type(
    client,
    reset_test_data,
):
    billing_event_id, _, _ = create_audit_test_event(
        client,
        "API-004",
        module="billing",
        event_type="payment_registered",
    )
    reception_event_id, _, _ = create_audit_test_event(
        client,
        "API-005",
        module="reception",
        event_type="check_in_completed",
    )

    module_response = client.get(
        "/audit/events",
        params={"module": "billing"},
    )
    event_type_response = client.get(
        "/audit/events",
        params={"event_type": "check_in_completed"},
    )

    assert module_response.status_code == 200
    assert event_type_response.status_code == 200

    module_event_ids = [event["id"] for event in module_response.json()]
    event_type_ids = [event["id"] for event in event_type_response.json()]

    assert billing_event_id in module_event_ids
    assert reception_event_id not in module_event_ids
    assert reception_event_id in event_type_ids
    assert billing_event_id not in event_type_ids


def test_audit_events_endpoint_respects_limit(
    client,
    reset_test_data,
):
    first_event_id, _, _ = create_audit_test_event(client, "API-006")
    second_event_id, _, _ = create_audit_test_event(client, "API-007")

    response = client.get("/audit/events", params={"limit": 1})

    assert response.status_code == 200

    events = response.json()

    assert len(events) == 1
    assert events[0]["id"] == second_event_id
    assert events[0]["id"] > first_event_id


def test_audit_events_endpoint_keeps_reception_events_endpoint_working(
    client,
    reset_test_data,
):
    event_id, reservation_id, _ = create_audit_test_event(
        client,
        "API-008",
    )

    response = client.get(
        f"/reception/reservations/{reservation_id}/events"
    )

    assert response.status_code == 200
    assert [event["id"] for event in response.json()] == [event_id]
