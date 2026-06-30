from pathlib import Path

from ceresa.db import get_connection
from ceresa.dev import seed_demo


def get_demo_counts() -> dict[str, int]:
    with get_connection() as connection:
        guests = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM guests
            WHERE guest_code LIKE 'CERESA-DEMO-GUEST-%'
            """
        ).fetchone()
        rooms = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM rooms
            WHERE room_number IN (
                'CERESA-DEMO-D101',
                'CERESA-DEMO-D102',
                'CERESA-DEMO-D201',
                'CERESA-DEMO-D202'
            )
            """
        ).fetchone()
        reservations = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM reservations
            WHERE reservation_code LIKE 'CERESA-DEMO-RES-%'
            """
        ).fetchone()
        billing_accounts = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM billing_accounts
            INNER JOIN reservations
                ON reservations.id = billing_accounts.reservation_id
            WHERE reservations.reservation_code LIKE 'CERESA-DEMO-RES-%'
            """
        ).fetchone()
        charges = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM billing_charges
            WHERE description LIKE 'CERESA-DEMO%'
            """
        ).fetchone()
        payments = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM billing_payments
            WHERE reference LIKE 'CERESA-DEMO%'
            """
        ).fetchone()
        audit_events = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM audit_events
            INNER JOIN reservations
                ON reservations.id = audit_events.reservation_id
            WHERE reservations.reservation_code = 'CERESA-DEMO-RES-001'
            """
        ).fetchone()

    return {
        "guests": int(guests["count"]),
        "rooms": int(rooms["count"]),
        "reservations": int(reservations["count"]),
        "billing_accounts": int(billing_accounts["count"]),
        "charges": int(charges["count"]),
        "payments": int(payments["count"]),
        "audit_events": int(audit_events["count"]),
    }


def get_demo_room(room_number: str) -> dict:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM rooms
            WHERE room_number = ?
            """,
            (room_number,),
        ).fetchone()

    return dict(row)


def get_demo_account_balance(reservation_code: str) -> int:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT billing_accounts.id
            FROM billing_accounts
            INNER JOIN reservations
                ON reservations.id = billing_accounts.reservation_id
            WHERE reservations.reservation_code = ?
            """,
            (reservation_code,),
        ).fetchone()

    account = seed_demo.billing_repository.get_billing_account_by_id(
        int(row["id"]),
    )

    return int(account["balance_cents"])


def test_seed_demo_runs_and_returns_manual_test_ids(reset_test_data):
    summary = seed_demo.seed_demo()

    assert summary.guests["CERESA-DEMO-GUEST-001"] > 0
    assert summary.guests["CERESA-DEMO-GUEST-002"] > 0
    assert summary.rooms["CERESA-DEMO-D101"] > 0
    assert summary.rooms["CERESA-DEMO-D202"] > 0
    assert summary.reservations["CERESA-DEMO-RES-001"] > 0
    assert summary.reservations["CERESA-DEMO-RES-002"] > 0
    assert (
        summary.billing_accounts["CERESA-DEMO-RES-001"]["balance_cents"]
        == 0
    )
    assert (
        summary.billing_accounts["CERESA-DEMO-RES-002"]["balance_cents"]
        > 0
    )


def test_seed_demo_is_idempotent(reset_test_data):
    first_summary = seed_demo.seed_demo()
    first_counts = get_demo_counts()

    second_summary = seed_demo.seed_demo()
    second_counts = get_demo_counts()

    assert second_counts == first_counts
    assert second_summary.guests == first_summary.guests
    assert second_summary.rooms == first_summary.rooms
    assert second_summary.reservations == first_summary.reservations
    assert second_counts["guests"] == 2
    assert second_counts["rooms"] == 4
    assert second_counts["reservations"] == 2
    assert second_counts["billing_accounts"] == 2
    assert second_counts["charges"] == 2
    assert second_counts["payments"] == 2


def test_seed_demo_creates_housekeeping_and_maintenance_rooms(
    reset_test_data,
):
    seed_demo.seed_demo()

    dirty_room = get_demo_room("CERESA-DEMO-D201")
    repair_room = get_demo_room("CERESA-DEMO-D202")

    assert dirty_room["cleaning_status"] == "dirty"
    assert repair_room["maintenance_status"] == "needs_repair"
    assert repair_room["room_status"] == "out_of_service"


def test_seed_demo_does_not_update_real_room_with_old_demo_number(
    reset_test_data,
):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO rooms (
                room_number,
                floor,
                room_type,
                room_status,
                cleaning_status,
                maintenance_status,
                has_jacuzzi,
                has_balcony,
                notes
            )
            VALUES (
                'D201',
                2,
                'Real Room',
                'available',
                'clean',
                'ok',
                0,
                0,
                'Real room must not be changed by seed.'
            )
            """
        )
        connection.commit()

    seed_demo.seed_demo()

    real_room = get_demo_room("D201")

    assert real_room["cleaning_status"] == "clean"
    assert real_room["maintenance_status"] == "ok"
    assert real_room["notes"] == "Real room must not be changed by seed."


def test_seed_demo_creates_billing_balances(reset_test_data):
    seed_demo.seed_demo()

    settled_balance = get_demo_account_balance("CERESA-DEMO-RES-001")
    open_balance = get_demo_account_balance("CERESA-DEMO-RES-002")

    assert settled_balance == 0
    assert open_balance == 50000


def test_seed_demo_generates_reception_audit_without_duplicates(
    reset_test_data,
):
    first_summary = seed_demo.seed_demo()
    second_summary = seed_demo.seed_demo()

    counts = get_demo_counts()

    assert first_summary.audit["created_events"] == [
        "check_in_completed",
        "check_out_completed",
    ]
    assert second_summary.audit["created_events"] == []
    assert counts["audit_events"] == 2


def test_seed_demo_has_no_frontend_dependency():
    seed_source = Path(seed_demo.__file__).read_text(encoding="utf-8")

    assert "frontend" not in seed_source.lower()


def test_seed_demo_does_not_touch_architecture_workflow_doc(
    reset_test_data,
):
    docs_path = Path("docs/architecture-workflow.html")
    existed_before = docs_path.exists()
    mtime_before = docs_path.stat().st_mtime_ns if existed_before else None

    seed_demo.seed_demo()

    assert docs_path.exists() is existed_before
    if existed_before:
        assert docs_path.stat().st_mtime_ns == mtime_before
