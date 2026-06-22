from ceresa.audit import repository as audit_repository
from ceresa.billing import repository as billing_repository
from ceresa.db import get_connection
from ceresa.reception import service


def create_reception_guest(client, suffix: str) -> int:
    response = client.post(
        "/guests",
        json={
            "guest_code": f"TEST-REC-GUEST-{suffix}",
            "first_name": "Reception",
            "last_name": "Guest",
            "email": None,
            "phone": None,
            "nationality": None,
            "notes": None,
        },
    )

    assert response.status_code == 200
    return response.json()["guest_id"]


def create_reception_room(client, suffix: str) -> int:
    response = client.post(
        "/rooms",
        json={
            "room_number": f"REC-{suffix[-3:]}",
            "floor": 1,
            "room_type": "Reception Test",
            "has_jacuzzi": False,
            "has_balcony": False,
            "notes": None,
        },
    )

    assert response.status_code == 200
    return response.json()["room_id"]


def create_reception_reservation(
    client,
    suffix: str,
    check_in_date: str = "2027-04-10",
    check_out_date: str = "2027-04-15",
    status: str = "confirmed",
) -> int:
    guest_id = create_reception_guest(client, suffix)
    room_id = create_reception_room(client, suffix)

    response = client.post(
        "/reservations",
        json={
            "reservation_code": f"TEST-REC-RES-{suffix}",
            "guest_id": guest_id,
            "room_id": room_id,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "status": status,
            "adults": 2,
            "children": 0,
            "notes": "Reservation created for reception tests.",
        },
    )

    assert response.status_code == 200
    return response.json()["reservation_id"]


def create_reception_actor_user(client, suffix: str) -> int:
    department_response = client.post(
        "/users/departments",
        json={
            "code": f"rec-{suffix.lower()}",
            "name": f"Reception {suffix}",
        },
    )

    assert department_response.status_code == 200

    user_response = client.post(
        "/users",
        json={
            "username": f"reception_actor_{suffix.lower()}",
            "full_name": "Reception Actor",
            "email": None,
            "user_type": "employee",
            "department_id": department_response.json()["department_id"],
        },
    )

    assert user_response.status_code == 200
    return user_response.json()["user_id"]


def cancel_reservation(reservation_id: int) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE reservations
            SET status = 'cancelled'
            WHERE id = ?
            """,
            (reservation_id,),
        )
        connection.commit()


def set_reservation_status(
    reservation_id: int,
    status: str,
) -> None:
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


def set_room_state(
    room_id: int,
    room_status: str | None = None,
    cleaning_status: str | None = None,
    maintenance_status: str | None = None,
) -> None:
    updates = []
    values = []

    if room_status is not None:
        updates.append("room_status = ?")
        values.append(room_status)

    if cleaning_status is not None:
        updates.append("cleaning_status = ?")
        values.append(cleaning_status)

    if maintenance_status is not None:
        updates.append("maintenance_status = ?")
        values.append(maintenance_status)

    values.append(room_id)

    with get_connection() as connection:
        connection.execute(
            f"""
            UPDATE rooms
            SET {", ".join(updates)}
            WHERE id = ?
            """,
            tuple(values),
        )
        connection.commit()


def get_reservation_state(reservation_id: int) -> dict:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, room_id, status
            FROM reservations
            WHERE id = ?
            """,
            (reservation_id,),
        ).fetchone()

    return dict(row)


def get_room_state(room_id: int) -> dict:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                id,
                room_status,
                cleaning_status,
                maintenance_status
            FROM rooms
            WHERE id = ?
            """,
            (room_id,),
        ).fetchone()

    return dict(row)


def get_billing_account_state(reservation_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, reservation_id, status
            FROM billing_accounts
            WHERE reservation_id = ?
            """,
            (reservation_id,),
        ).fetchone()

    return dict(row) if row else None


def list_audit_events_for_reservation(reservation_id: int) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                event_type,
                reservation_id,
                room_id,
                billing_account_id,
                actor_user_id,
                before_state_json,
                after_state_json
            FROM audit_events
            WHERE reservation_id = ?
            ORDER BY id
            """,
            (reservation_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def create_billing_account_for_reservation(
    client,
    reservation_id: int,
) -> int:
    response = client.post(
        "/billing/accounts",
        json={
            "reservation_id": reservation_id,
            "notes": None,
        },
    )

    assert response.status_code == 201
    return response.json()["billing_account_id"]


def add_billing_charge(
    client,
    account_id: int,
    amount_cents: int,
) -> None:
    response = client.post(
        f"/billing/accounts/{account_id}/charges",
        json={
            "source_module": "rooms",
            "description": "Reception test charge",
            "amount_cents": amount_cents,
        },
    )

    assert response.status_code == 201


def add_billing_payment(
    client,
    account_id: int,
    amount_cents: int,
) -> None:
    response = client.post(
        f"/billing/accounts/{account_id}/payments",
        json={
            "payment_method": "card",
            "amount_cents": amount_cents,
            "reference": "RECEPTION-TEST",
        },
    )

    assert response.status_code == 201


def disable_billing(monkeypatch) -> None:
    original_is_module_enabled = service.module_loader.is_module_enabled

    def fake_is_module_enabled(module_name: str) -> bool:
        if module_name == "billing":
            return False

        return original_is_module_enabled(module_name)

    monkeypatch.setattr(
        service.module_loader,
        "is_module_enabled",
        fake_is_module_enabled,
    )


def test_reception_status(client):
    response = client.get("/reception/status")

    assert response.status_code == 200

    data = response.json()

    assert data["module"] == "reception"
    assert data["status"] == "active"
    assert data["message"] == "Reception module is running"


def test_reception_module_is_loaded(client):
    response = client.get("/system/modules")

    assert response.status_code == 200

    modules = response.json()
    reception_module = next(
        module for module in modules if module["name"] == "reception"
    )

    assert reception_module["enabled"] is True
    assert reception_module["implemented"] is True
    assert reception_module["loaded"] is True
    assert reception_module["error"] is None


def test_arrivals_returns_empty_list_when_no_reservations(
    client,
    reset_test_data,
):
    response = client.get(
        "/reception/arrivals",
        params={"arrival_date": "2027-04-10"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_arrivals_includes_confirmed_reservation(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(
        client,
        "ARR-001",
        check_in_date="2027-04-10",
        check_out_date="2027-04-15",
    )

    response = client.get(
        "/reception/arrivals",
        params={"arrival_date": "2027-04-10"},
    )

    assert response.status_code == 200

    arrivals = response.json()

    assert len(arrivals) == 1
    assert arrivals[0]["id"] == reservation_id
    assert arrivals[0]["reservation_code"] == "TEST-REC-RES-ARR-001"
    assert arrivals[0]["guest_first_name"] == "Reception"
    assert arrivals[0]["room_number"] == "REC-001"


def test_arrivals_excludes_cancelled_reservation(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(
        client,
        "ARR-002",
        check_in_date="2027-04-10",
        check_out_date="2027-04-15",
    )
    cancel_reservation(reservation_id)

    response = client.get(
        "/reception/arrivals",
        params={"arrival_date": "2027-04-10"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_departures_returns_empty_list_when_no_reservations(
    client,
    reset_test_data,
):
    response = client.get(
        "/reception/departures",
        params={"departure_date": "2027-04-15"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_departures_includes_valid_reservation(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(
        client,
        "DEP-001",
        check_in_date="2027-04-10",
        check_out_date="2027-04-15",
    )

    response = client.get(
        "/reception/departures",
        params={"departure_date": "2027-04-15"},
    )

    assert response.status_code == 200

    departures = response.json()

    assert len(departures) == 1
    assert departures[0]["id"] == reservation_id
    assert departures[0]["reservation_code"] == "TEST-REC-RES-DEP-001"
    assert departures[0]["guest_last_name"] == "Guest"
    assert departures[0]["room_number"] == "REC-001"


def test_reservation_summary_returns_404_for_missing_reservation(
    client,
    reset_test_data,
):
    response = client.get(
        "/reception/reservations/999999/summary"
    )

    assert response.status_code == 404


def test_reservation_summary_works_with_billing_enabled_without_account(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(
        client,
        "SUM-001",
    )

    response = client.get(
        f"/reception/reservations/{reservation_id}/summary"
    )

    assert response.status_code == 200

    summary = response.json()

    assert summary["reservation"]["id"] == reservation_id
    assert summary["billing_enabled"] is True
    assert summary["billing_account"] is None


def test_reservation_summary_includes_billing_account_balance_and_currency(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(
        client,
        "SUM-002",
    )

    account_response = client.post(
        "/billing/accounts",
        json={
            "reservation_id": reservation_id,
            "notes": None,
        },
    )
    account_id = account_response.json()["billing_account_id"]

    charge_response = client.post(
        f"/billing/accounts/{account_id}/charges",
        json={
            "source_module": "rooms",
            "description": "Accommodation",
            "amount_cents": 20000,
        },
    )
    payment_response = client.post(
        f"/billing/accounts/{account_id}/payments",
        json={
            "payment_method": "card",
            "amount_cents": 15000,
            "reference": "REC-SUM-002",
        },
    )

    assert account_response.status_code == 201
    assert charge_response.status_code == 201
    assert payment_response.status_code == 201

    response = client.get(
        f"/reception/reservations/{reservation_id}/summary"
    )

    assert response.status_code == 200

    billing_account = response.json()["billing_account"]

    assert billing_account["id"] == account_id
    assert billing_account["charges_total_cents"] == 20000
    assert billing_account["payments_total_cents"] == 15000
    assert billing_account["balance_cents"] == 5000
    assert billing_account["currency"] == "EUR"
    assert len(billing_account["charges"]) == 1
    assert len(billing_account["payments"]) == 1


def test_reservation_summary_works_when_billing_is_disabled(
    client,
    reset_test_data,
    monkeypatch,
):
    reservation_id = create_reception_reservation(
        client,
        "SUM-003",
    )
    original_is_module_enabled = service.module_loader.is_module_enabled

    def fake_is_module_enabled(module_name: str) -> bool:
        if module_name == "billing":
            return False

        return original_is_module_enabled(module_name)

    monkeypatch.setattr(
        service.module_loader,
        "is_module_enabled",
        fake_is_module_enabled,
    )

    response = client.get(
        f"/reception/reservations/{reservation_id}/summary"
    )

    assert response.status_code == 200

    summary = response.json()

    assert summary["reservation"]["id"] == reservation_id
    assert summary["billing_enabled"] is False
    assert summary["billing_account"] is None


def test_optional_billing_error_does_not_break_reception_status(
    client,
    reset_test_data,
    monkeypatch,
):
    reservation_id = create_reception_reservation(
        client,
        "SUM-004",
    )

    def fail_get_billing_account_by_reservation_id(
        reservation_id: int,
    ) -> dict:
        raise RuntimeError("billing unavailable")

    monkeypatch.setattr(
        billing_repository,
        "get_billing_account_by_reservation_id",
        fail_get_billing_account_by_reservation_id,
    )

    summary_response = client.get(
        f"/reception/reservations/{reservation_id}/summary"
    )
    status_response = client.get("/reception/status")

    assert summary_response.status_code == 503
    assert status_response.status_code == 200


def test_check_in_updates_reservation_and_room(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(client, "CI-001")

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-in"
    )

    assert response.status_code == 200

    data = response.json()
    reservation = get_reservation_state(reservation_id)
    room = get_room_state(data["room_id"])

    assert data["reservation_status"] == "checked_in"
    assert data["room_status"] == "occupied"
    assert reservation["status"] == "checked_in"
    assert room["room_status"] == "occupied"


def test_check_in_creates_billing_account_when_enabled(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(client, "CI-002")

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-in"
    )

    assert response.status_code == 200

    data = response.json()
    account = get_billing_account_state(reservation_id)

    assert data["billing_enabled"] is True
    assert data["billing_account_id"] == account["id"]
    assert account["status"] == "open"


def test_check_in_reuses_open_billing_account(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(client, "CI-003")
    account_id = create_billing_account_for_reservation(
        client,
        reservation_id,
    )

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-in"
    )

    assert response.status_code == 200
    assert response.json()["billing_account_id"] == account_id


def test_check_in_works_when_billing_is_disabled(
    client,
    reset_test_data,
    monkeypatch,
):
    reservation_id = create_reception_reservation(client, "CI-004")
    disable_billing(monkeypatch)

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-in"
    )

    assert response.status_code == 200
    assert response.json()["billing_enabled"] is False
    assert response.json()["billing_account_id"] is None
    assert get_billing_account_state(reservation_id) is None


def test_pending_reservation_cannot_check_in(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(
        client,
        "CI-005",
        status="pending",
    )

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-in"
    )

    assert response.status_code == 409


def test_cancelled_reservation_cannot_check_in(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(client, "CI-006")
    cancel_reservation(reservation_id)

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-in"
    )

    assert response.status_code == 409


def test_checked_in_reservation_cannot_check_in_again(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(client, "CI-007")

    first_response = client.post(
        f"/reception/reservations/{reservation_id}/check-in"
    )
    second_response = client.post(
        f"/reception/reservations/{reservation_id}/check-in"
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409


def test_dirty_room_blocks_check_in(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(client, "CI-008")
    room_id = get_reservation_state(reservation_id)["room_id"]
    set_room_state(room_id, cleaning_status="dirty")

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-in"
    )

    assert response.status_code == 409


def test_occupied_room_blocks_check_in(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(client, "CI-009")
    room_id = get_reservation_state(reservation_id)["room_id"]
    set_room_state(room_id, room_status="occupied")

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-in"
    )

    assert response.status_code == 409


def test_room_with_maintenance_issue_blocks_check_in(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(client, "CI-010")
    room_id = get_reservation_state(reservation_id)["room_id"]
    set_room_state(room_id, maintenance_status="needs_repair")

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-in"
    )

    assert response.status_code == 409


def test_billing_operational_failure_rolls_back_check_in(
    client,
    reset_test_data,
    monkeypatch,
):
    reservation_id = create_reception_reservation(client, "CI-011")
    room_id = get_reservation_state(reservation_id)["room_id"]

    def fail_create_account(
        connection,
        reservation_id: int,
        notes: str | None,
    ) -> int:
        raise RuntimeError("billing write failed")

    monkeypatch.setattr(
        billing_repository,
        "create_billing_account_with_connection",
        fail_create_account,
    )

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-in"
    )

    assert response.status_code == 503
    assert get_reservation_state(reservation_id)["status"] == "confirmed"
    assert get_room_state(room_id)["room_status"] == "available"
    assert get_billing_account_state(reservation_id) is None


def test_check_out_with_zero_balance_closes_account_and_releases_room(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(client, "CO-001")
    check_in_response = client.post(
        f"/reception/reservations/{reservation_id}/check-in"
    )
    room_id = check_in_response.json()["room_id"]

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-out"
    )

    assert response.status_code == 200

    data = response.json()
    reservation = get_reservation_state(reservation_id)
    room = get_room_state(room_id)
    account = get_billing_account_state(reservation_id)

    assert data["reservation_status"] == "checked_out"
    assert data["room_status"] == "available"
    assert data["cleaning_status"] == "dirty"
    assert data["billing_account_status"] == "closed"
    assert reservation["status"] == "checked_out"
    assert room["room_status"] == "available"
    assert room["cleaning_status"] == "dirty"
    assert account["status"] == "closed"


def test_check_out_with_positive_balance_is_rejected(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(client, "CO-002")
    check_in_response = client.post(
        f"/reception/reservations/{reservation_id}/check-in"
    )
    account_id = check_in_response.json()["billing_account_id"]
    add_billing_charge(client, account_id, 1000)

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-out"
    )

    assert response.status_code == 409


def test_check_out_with_negative_balance_is_rejected(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(client, "CO-003")
    check_in_response = client.post(
        f"/reception/reservations/{reservation_id}/check-in"
    )
    account_id = check_in_response.json()["billing_account_id"]
    add_billing_payment(client, account_id, 1000)

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-out"
    )

    assert response.status_code == 409


def test_check_out_without_billing_account_is_rejected_when_billing_enabled(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(client, "CO-004")
    room_id = get_reservation_state(reservation_id)["room_id"]
    set_reservation_status(reservation_id, "checked_in")
    set_room_state(room_id, room_status="occupied")

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-out"
    )

    assert response.status_code == 409


def test_check_out_works_when_billing_is_disabled(
    client,
    reset_test_data,
    monkeypatch,
):
    reservation_id = create_reception_reservation(client, "CO-005")
    room_id = get_reservation_state(reservation_id)["room_id"]
    set_reservation_status(reservation_id, "checked_in")
    set_room_state(room_id, room_status="occupied")
    disable_billing(monkeypatch)

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-out"
    )

    assert response.status_code == 200
    assert response.json()["billing_enabled"] is False
    assert get_reservation_state(reservation_id)["status"] == "checked_out"
    assert get_room_state(room_id)["room_status"] == "available"


def test_reservation_not_checked_in_cannot_check_out(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(client, "CO-006")

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-out"
    )

    assert response.status_code == 409


def test_repeated_check_out_is_rejected(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(client, "CO-007")
    client.post(f"/reception/reservations/{reservation_id}/check-in")

    first_response = client.post(
        f"/reception/reservations/{reservation_id}/check-out"
    )
    second_response = client.post(
        f"/reception/reservations/{reservation_id}/check-out"
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409


def test_room_not_occupied_blocks_check_out(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(client, "CO-008")
    room_id = get_reservation_state(reservation_id)["room_id"]
    set_reservation_status(reservation_id, "checked_in")

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-out"
    )

    assert response.status_code == 409
    assert get_room_state(room_id)["room_status"] == "available"


def test_check_out_sends_room_out_of_service_when_repair_is_needed(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(client, "CO-009")
    check_in_response = client.post(
        f"/reception/reservations/{reservation_id}/check-in"
    )
    room_id = check_in_response.json()["room_id"]
    set_room_state(room_id, maintenance_status="needs_repair")

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-out"
    )

    assert response.status_code == 200

    room = get_room_state(room_id)

    assert room["room_status"] == "out_of_service"
    assert room["cleaning_status"] == "dirty"
    assert room["maintenance_status"] == "needs_repair"


def test_check_out_final_update_failure_rolls_back_all_changes(
    client,
    reset_test_data,
    monkeypatch,
):
    reservation_id = create_reception_reservation(client, "CO-010")
    check_in_response = client.post(
        f"/reception/reservations/{reservation_id}/check-in"
    )
    room_id = check_in_response.json()["room_id"]

    def fail_close_account(connection, billing_account_id: int) -> None:
        raise RuntimeError("final billing update failed")

    monkeypatch.setattr(
        billing_repository,
        "close_billing_account_with_connection",
        fail_close_account,
    )

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-out"
    )

    assert response.status_code == 503

    reservation = get_reservation_state(reservation_id)
    room = get_room_state(room_id)
    account = get_billing_account_state(reservation_id)

    assert reservation["status"] == "checked_in"
    assert room["room_status"] == "occupied"
    assert room["cleaning_status"] == "clean"
    assert account["status"] == "open"


def test_successful_check_in_creates_one_audit_event(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(client, "AU-001")

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-in"
    )

    assert response.status_code == 200

    events = list_audit_events_for_reservation(reservation_id)

    assert len(events) == 1
    assert events[0]["event_type"] == "check_in_completed"
    assert events[0]["reservation_id"] == reservation_id
    assert events[0]["room_id"] == response.json()["room_id"]
    assert events[0]["billing_account_id"] == response.json()[
        "billing_account_id"
    ]
    assert events[0]["actor_user_id"] is None


def test_check_in_with_actor_user_id_creates_audit_event_with_actor(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(client, "AU-011")
    actor_user_id = create_reception_actor_user(client, "AU-CI-011")

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-in",
        json={"actor_user_id": actor_user_id},
    )

    assert response.status_code == 200

    events = list_audit_events_for_reservation(reservation_id)

    assert len(events) == 1
    assert events[0]["event_type"] == "check_in_completed"
    assert events[0]["actor_user_id"] == actor_user_id


def test_check_in_with_missing_actor_user_id_is_rejected_and_rolls_back(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(client, "AU-012")
    room_id = get_reservation_state(reservation_id)["room_id"]

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-in",
        json={"actor_user_id": 999999},
    )

    assert response.status_code == 404
    assert get_reservation_state(reservation_id)["status"] == "confirmed"
    assert get_room_state(room_id)["room_status"] == "available"
    assert get_billing_account_state(reservation_id) is None
    assert list_audit_events_for_reservation(reservation_id) == []


def test_check_in_audit_event_contains_before_and_after_state(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(client, "AU-002")

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-in"
    )

    assert response.status_code == 200

    event_response = client.get(
        f"/reception/reservations/{reservation_id}/events"
    )
    event = event_response.json()[0]

    assert event["before_state"]["reservation_status"] == "confirmed"
    assert event["before_state"]["room_status"] == "available"
    assert event["before_state"]["cleaning_status"] == "clean"
    assert event["before_state"]["maintenance_status"] == "ok"
    assert "billing_account_status" not in event["before_state"]
    assert event["after_state"]["reservation_status"] == "checked_in"
    assert event["after_state"]["room_status"] == "occupied"
    assert event["after_state"]["cleaning_status"] == "clean"
    assert event["after_state"]["maintenance_status"] == "ok"
    assert event["after_state"]["billing_account_status"] == "open"


def test_successful_check_out_creates_second_audit_event_in_order(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(client, "AU-003")
    client.post(f"/reception/reservations/{reservation_id}/check-in")

    check_out_response = client.post(
        f"/reception/reservations/{reservation_id}/check-out"
    )

    assert check_out_response.status_code == 200

    event_response = client.get(
        f"/reception/reservations/{reservation_id}/events"
    )
    events = event_response.json()

    assert [event["event_type"] for event in events] == [
        "check_in_completed",
        "check_out_completed",
    ]
    assert events[0]["id"] < events[1]["id"]
    assert events[1]["before_state"]["reservation_status"] == "checked_in"
    assert events[1]["after_state"]["reservation_status"] == "checked_out"
    assert events[1]["after_state"]["cleaning_status"] == "dirty"
    assert events[1]["after_state"]["billing_account_status"] == "closed"
    assert events[1]["actor_user_id"] is None


def test_check_out_with_actor_user_id_creates_audit_event_with_actor(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(client, "AU-013")
    actor_user_id = create_reception_actor_user(client, "AU-CO-013")
    client.post(f"/reception/reservations/{reservation_id}/check-in")

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-out",
        json={"actor_user_id": actor_user_id},
    )

    assert response.status_code == 200

    events = list_audit_events_for_reservation(reservation_id)

    assert [event["event_type"] for event in events] == [
        "check_in_completed",
        "check_out_completed",
    ]
    assert events[1]["actor_user_id"] == actor_user_id


def test_check_out_with_missing_actor_user_id_is_rejected_and_rolls_back(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(client, "AU-014")
    check_in_response = client.post(
        f"/reception/reservations/{reservation_id}/check-in"
    )
    room_id = check_in_response.json()["room_id"]

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-out",
        json={"actor_user_id": 999999},
    )

    events = list_audit_events_for_reservation(reservation_id)
    account = get_billing_account_state(reservation_id)

    assert response.status_code == 404
    assert get_reservation_state(reservation_id)["status"] == "checked_in"
    assert get_room_state(room_id)["room_status"] == "occupied"
    assert get_room_state(room_id)["cleaning_status"] == "clean"
    assert account["status"] == "open"
    assert [event["event_type"] for event in events] == [
        "check_in_completed"
    ]


def test_reception_mvp_end_to_end_flow_with_actor_user(
    client,
    reset_test_data,
):
    guest_response = client.post(
        "/guests",
        json={
            "guest_code": "MVP-GUEST-001",
            "first_name": "MVP",
            "last_name": "Guest",
            "email": "mvp.guest@example.com",
            "phone": None,
            "nationality": "AR",
            "notes": "End-to-end reception MVP test.",
        },
    )
    room_response = client.post(
        "/rooms",
        json={
            "room_number": "MVP-101",
            "floor": 1,
            "room_type": "MVP Suite",
            "has_jacuzzi": False,
            "has_balcony": True,
            "notes": None,
        },
    )

    assert guest_response.status_code == 200
    assert room_response.status_code == 200

    guest_id = guest_response.json()["guest_id"]
    room_id = room_response.json()["room_id"]
    actor_user_id = create_reception_actor_user(client, "MVP-001")

    reservation_response = client.post(
        "/reservations",
        json={
            "reservation_code": "MVP-RES-001",
            "guest_id": guest_id,
            "room_id": room_id,
            "check_in_date": "2027-06-01",
            "check_out_date": "2027-06-05",
            "status": "confirmed",
            "adults": 2,
            "children": 0,
            "notes": "MVP end-to-end reservation.",
        },
    )

    assert reservation_response.status_code == 200
    reservation_id = reservation_response.json()["reservation_id"]

    account_response = client.post(
        "/billing/accounts",
        json={
            "reservation_id": reservation_id,
            "notes": "MVP billing account.",
        },
    )

    assert account_response.status_code == 201
    account_id = account_response.json()["billing_account_id"]

    charge_response = client.post(
        f"/billing/accounts/{account_id}/charges",
        json={
            "source_module": "rooms",
            "description": "Accommodation package",
            "amount_cents": 50000,
        },
    )
    payment_response = client.post(
        f"/billing/accounts/{account_id}/payments",
        json={
            "payment_method": "card",
            "amount_cents": 50000,
            "reference": "MVP-PAY-001",
        },
    )

    assert charge_response.status_code == 201
    assert payment_response.status_code == 201

    summary_before = client.get(
        f"/reception/reservations/{reservation_id}/summary"
    )
    assert summary_before.status_code == 200
    before_data = summary_before.json()
    assert before_data["reservation"]["id"] == reservation_id
    assert before_data["billing_account"]["id"] == account_id
    assert before_data["billing_account"]["balance_cents"] == 0

    check_in_response = client.post(
        f"/reception/reservations/{reservation_id}/check-in",
        json={"actor_user_id": actor_user_id},
    )
    assert check_in_response.status_code == 200
    assert check_in_response.json()["reservation_status"] == "checked_in"

    summary_after_check_in = client.get(
        f"/reception/reservations/{reservation_id}/summary"
    )
    assert summary_after_check_in.status_code == 200
    assert (
        summary_after_check_in.json()["reservation"]["status"]
        == "checked_in"
    )

    check_out_response = client.post(
        f"/reception/reservations/{reservation_id}/check-out",
        json={"actor_user_id": actor_user_id},
    )
    assert check_out_response.status_code == 200
    assert check_out_response.json()["reservation_status"] == "checked_out"

    events_response = client.get(
        f"/reception/reservations/{reservation_id}/events"
    )
    assert events_response.status_code == 200
    events = events_response.json()

    reservation = get_reservation_state(reservation_id)
    room = get_room_state(room_id)
    account = get_billing_account_state(reservation_id)

    assert reservation["status"] == "checked_out"
    assert room["room_status"] == "available"
    assert room["cleaning_status"] == "dirty"
    assert account["status"] == "closed"
    assert [event["event_type"] for event in events] == [
        "check_in_completed",
        "check_out_completed",
    ]
    assert events[0]["actor_user_id"] == actor_user_id
    assert events[1]["actor_user_id"] == actor_user_id


def test_failed_check_in_does_not_create_audit_event(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(
        client,
        "AU-004",
        status="pending",
    )

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-in"
    )

    assert response.status_code == 409
    assert list_audit_events_for_reservation(reservation_id) == []


def test_rejected_check_out_with_pending_balance_does_not_create_event(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(client, "AU-005")
    check_in_response = client.post(
        f"/reception/reservations/{reservation_id}/check-in"
    )
    account_id = check_in_response.json()["billing_account_id"]
    add_billing_charge(client, account_id, 1000)

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-out"
    )

    events = list_audit_events_for_reservation(reservation_id)

    assert response.status_code == 409
    assert [event["event_type"] for event in events] == [
        "check_in_completed"
    ]


def test_check_out_with_billing_disabled_creates_event_without_account(
    client,
    reset_test_data,
    monkeypatch,
):
    reservation_id = create_reception_reservation(client, "AU-006")
    room_id = get_reservation_state(reservation_id)["room_id"]
    set_reservation_status(reservation_id, "checked_in")
    set_room_state(room_id, room_status="occupied")
    disable_billing(monkeypatch)

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-out"
    )

    assert response.status_code == 200

    events = list_audit_events_for_reservation(reservation_id)

    assert len(events) == 1
    assert events[0]["event_type"] == "check_out_completed"
    assert events[0]["billing_account_id"] is None


def test_reservation_events_returns_empty_list_without_events(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(client, "AU-007")

    response = client.get(
        f"/reception/reservations/{reservation_id}/events"
    )

    assert response.status_code == 200
    assert response.json() == []


def test_reservation_events_returns_404_for_missing_reservation(
    client,
    reset_test_data,
):
    response = client.get("/reception/reservations/999999/events")

    assert response.status_code == 404


def test_audit_insert_failure_rolls_back_check_in(
    client,
    reset_test_data,
    monkeypatch,
):
    reservation_id = create_reception_reservation(client, "AU-008")
    room_id = get_reservation_state(reservation_id)["room_id"]

    def fail_create_event(connection, event_data: dict) -> int:
        raise RuntimeError("audit insert failed")

    monkeypatch.setattr(
        audit_repository,
        "create_audit_event_with_connection",
        fail_create_event,
    )

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-in"
    )

    assert response.status_code == 503
    assert get_reservation_state(reservation_id)["status"] == "confirmed"
    assert get_room_state(room_id)["room_status"] == "available"
    assert get_billing_account_state(reservation_id) is None
    assert list_audit_events_for_reservation(reservation_id) == []


def test_audit_insert_failure_rolls_back_check_out(
    client,
    reset_test_data,
    monkeypatch,
):
    reservation_id = create_reception_reservation(client, "AU-009")
    check_in_response = client.post(
        f"/reception/reservations/{reservation_id}/check-in"
    )
    room_id = check_in_response.json()["room_id"]

    def fail_create_event(connection, event_data: dict) -> int:
        raise RuntimeError("audit insert failed")

    monkeypatch.setattr(
        audit_repository,
        "create_audit_event_with_connection",
        fail_create_event,
    )

    response = client.post(
        f"/reception/reservations/{reservation_id}/check-out"
    )

    events = list_audit_events_for_reservation(reservation_id)
    account = get_billing_account_state(reservation_id)

    assert response.status_code == 503
    assert get_reservation_state(reservation_id)["status"] == "checked_in"
    assert get_room_state(room_id)["room_status"] == "occupied"
    assert get_room_state(room_id)["cleaning_status"] == "clean"
    assert account["status"] == "open"
    assert [event["event_type"] for event in events] == [
        "check_in_completed"
    ]


def test_audit_states_are_returned_as_json_objects(
    client,
    reset_test_data,
):
    reservation_id = create_reception_reservation(client, "AU-010")
    client.post(f"/reception/reservations/{reservation_id}/check-in")

    response = client.get(
        f"/reception/reservations/{reservation_id}/events"
    )
    event = response.json()[0]

    assert isinstance(event["before_state"], dict)
    assert isinstance(event["after_state"], dict)
    assert isinstance(event["metadata"], dict)


def test_audit_events_are_not_mutable_from_api(client):
    routes = [
        route
        for route in client.app.routes
        if "/events" in getattr(route, "path", "")
    ]
    mutable_methods = {
        method
        for route in routes
        for method in route.methods
        if method in {"DELETE", "PATCH", "POST", "PUT"}
    }

    assert mutable_methods == set()
