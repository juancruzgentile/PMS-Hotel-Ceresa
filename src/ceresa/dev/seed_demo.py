"""Local-only CERESA demo data seed tool.

This module is intended for development and manual MVP testing. It is not
loaded by FastAPI, does not create HTTP endpoints, and only creates or updates
records with explicit CERESA demo identifiers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI

from ceresa.billing import repository as billing_repository
from ceresa.core import module_loader
from ceresa.db import get_connection, initialize_database
from ceresa.reception import service as reception_service


DEMO_PREFIX = "CERESA-DEMO"

DEMO_GUESTS = [
    {
        "guest_code": "CERESA-DEMO-GUEST-001",
        "first_name": "Ceresa",
        "last_name": "Demo Guest One",
        "email": None,
        "phone": None,
        "nationality": "Demo",
        "notes": "CERESA-DEMO local development guest.",
    },
    {
        "guest_code": "CERESA-DEMO-GUEST-002",
        "first_name": "Ceresa",
        "last_name": "Demo Guest Two",
        "email": None,
        "phone": None,
        "nationality": "Demo",
        "notes": "CERESA-DEMO local development guest.",
    },
]

DEMO_ROOMS = [
    {
        "room_number": "CERESA-DEMO-D101",
        "floor": 1,
        "room_type": "CERESA-DEMO Standard",
        "room_status": "available",
        "cleaning_status": "clean",
        "maintenance_status": "ok",
        "has_jacuzzi": 0,
        "has_balcony": 1,
        "notes": "CERESA-DEMO clean operational room.",
    },
    {
        "room_number": "CERESA-DEMO-D102",
        "floor": 1,
        "room_type": "CERESA-DEMO Standard",
        "room_status": "available",
        "cleaning_status": "clean",
        "maintenance_status": "ok",
        "has_jacuzzi": 0,
        "has_balcony": 0,
        "notes": "CERESA-DEMO room for open reservation.",
    },
    {
        "room_number": "CERESA-DEMO-D201",
        "floor": 2,
        "room_type": "CERESA-DEMO Suite",
        "room_status": "available",
        "cleaning_status": "dirty",
        "maintenance_status": "ok",
        "has_jacuzzi": 1,
        "has_balcony": 1,
        "notes": "CERESA-DEMO dirty room for Housekeeping.",
    },
    {
        "room_number": "CERESA-DEMO-D202",
        "floor": 2,
        "room_type": "CERESA-DEMO Suite",
        "room_status": "out_of_service",
        "cleaning_status": "clean",
        "maintenance_status": "needs_repair",
        "has_jacuzzi": 0,
        "has_balcony": 1,
        "notes": "CERESA-DEMO repair room for Maintenance.",
    },
]

DEMO_RESERVATIONS = [
    {
        "reservation_code": "CERESA-DEMO-RES-001",
        "guest_code": "CERESA-DEMO-GUEST-001",
        "room_number": "CERESA-DEMO-D101",
        "check_in_date": "2027-01-10",
        "check_out_date": "2027-01-12",
        "status": "confirmed",
        "adults": 2,
        "children": 0,
        "notes": "CERESA-DEMO settled reception flow reservation.",
    },
    {
        "reservation_code": "CERESA-DEMO-RES-002",
        "guest_code": "CERESA-DEMO-GUEST-002",
        "room_number": "CERESA-DEMO-D102",
        "check_in_date": "2027-01-20",
        "check_out_date": "2027-01-23",
        "status": "confirmed",
        "adults": 1,
        "children": 0,
        "notes": "CERESA-DEMO open balance reservation.",
    },
]


@dataclass
class SeedSummary:
    guests: dict[str, int]
    rooms: dict[str, int]
    reservations: dict[str, int]
    billing_accounts: dict[str, dict[str, int]]
    audit: dict[str, Any]


def _fetch_one_by_value(
    connection: Any,
    table_name: str,
    column_name: str,
    value: str,
) -> dict[str, Any] | None:
    row = connection.execute(
        f"""
        SELECT *
        FROM {table_name}
        WHERE {column_name} = ?
        """,
        (value,),
    ).fetchone()

    return dict(row) if row else None


def _ensure_guest(connection: Any, guest_data: dict[str, Any]) -> int:
    existing_guest = _fetch_one_by_value(
        connection,
        "guests",
        "guest_code",
        guest_data["guest_code"],
    )

    if existing_guest is not None:
        return int(existing_guest["id"])

    cursor = connection.execute(
        """
        INSERT INTO guests (
            guest_code,
            first_name,
            last_name,
            email,
            phone,
            nationality,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            guest_data["guest_code"],
            guest_data["first_name"],
            guest_data["last_name"],
            guest_data.get("email"),
            guest_data.get("phone"),
            guest_data.get("nationality"),
            guest_data.get("notes"),
        ),
    )

    return int(cursor.lastrowid)


def _ensure_room(connection: Any, room_data: dict[str, Any]) -> int:
    existing_room = _fetch_one_by_value(
        connection,
        "rooms",
        "room_number",
        room_data["room_number"],
    )

    if existing_room is not None:
        if room_data["room_number"].startswith(DEMO_PREFIX):
            connection.execute(
                """
                UPDATE rooms
                SET
                    room_status = ?,
                    cleaning_status = ?,
                    maintenance_status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    room_data["room_status"],
                    room_data["cleaning_status"],
                    room_data["maintenance_status"],
                    existing_room["id"],
                ),
            )

        return int(existing_room["id"])

    cursor = connection.execute(
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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            room_data["room_number"],
            room_data["floor"],
            room_data["room_type"],
            room_data["room_status"],
            room_data["cleaning_status"],
            room_data["maintenance_status"],
            room_data["has_jacuzzi"],
            room_data["has_balcony"],
            room_data["notes"],
        ),
    )

    return int(cursor.lastrowid)


def _ensure_reservation(
    connection: Any,
    reservation_data: dict[str, Any],
    guest_ids: dict[str, int],
    room_ids: dict[str, int],
) -> int:
    existing_reservation = _fetch_one_by_value(
        connection,
        "reservations",
        "reservation_code",
        reservation_data["reservation_code"],
    )

    if existing_reservation is not None:
        return int(existing_reservation["id"])

    cursor = connection.execute(
        """
        INSERT INTO reservations (
            reservation_code,
            guest_id,
            room_id,
            check_in_date,
            check_out_date,
            status,
            adults,
            children,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            reservation_data["reservation_code"],
            guest_ids[reservation_data["guest_code"]],
            room_ids[reservation_data["room_number"]],
            reservation_data["check_in_date"],
            reservation_data["check_out_date"],
            reservation_data["status"],
            reservation_data["adults"],
            reservation_data["children"],
            reservation_data["notes"],
        ),
    )

    return int(cursor.lastrowid)


def _ensure_billing_account(connection: Any, reservation_id: int) -> int:
    existing_account = (
        billing_repository.get_billing_account_by_reservation_id_with_connection(
            connection,
            reservation_id,
        )
    )

    if existing_account is not None:
        return int(existing_account["id"])

    return billing_repository.create_billing_account_with_connection(
        connection,
        reservation_id,
        "CERESA-DEMO local development billing account.",
    )


def _ensure_charge(
    connection: Any,
    billing_account_id: int,
    description: str,
    amount_cents: int,
) -> None:
    row = connection.execute(
        """
        SELECT id
        FROM billing_charges
        WHERE billing_account_id = ?
          AND source_module = 'rooms'
          AND description = ?
        """,
        (
            billing_account_id,
            description,
        ),
    ).fetchone()

    if row is not None:
        return

    connection.execute(
        """
        INSERT INTO billing_charges (
            billing_account_id,
            source_module,
            description,
            amount_cents
        )
        VALUES (?, 'rooms', ?, ?)
        """,
        (
            billing_account_id,
            description,
            amount_cents,
        ),
    )


def _ensure_payment(
    connection: Any,
    billing_account_id: int,
    reference: str,
    amount_cents: int,
) -> None:
    row = connection.execute(
        """
        SELECT id
        FROM billing_payments
        WHERE billing_account_id = ?
          AND reference = ?
        """,
        (
            billing_account_id,
            reference,
        ),
    ).fetchone()

    if row is not None:
        return

    connection.execute(
        """
        INSERT INTO billing_payments (
            billing_account_id,
            payment_method,
            amount_cents,
            reference
        )
        VALUES (?, 'card', ?, ?)
        """,
        (
            billing_account_id,
            amount_cents,
            reference,
        ),
    )


def _get_reservation_status(reservation_id: int) -> str:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT status
            FROM reservations
            WHERE id = ?
            """,
            (reservation_id,),
        ).fetchone()

    return str(row["status"])


def _prepare_reception_demo_room(room_id: int) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE rooms
            SET
                room_status = 'available',
                cleaning_status = 'clean',
                maintenance_status = 'ok',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
              AND room_number = 'CERESA-DEMO-D101'
            """,
            (room_id,),
        )
        connection.commit()


def _ensure_modules_loaded_for_reception() -> None:
    required_modules = {
        "audit",
        "billing",
        "reservations",
        "rooms",
        "users",
    }

    if required_modules.issubset(module_loader.LOADED_MODULES):
        return

    module_loader.load_enabled_modules(FastAPI())


def _create_reception_audit_if_possible(
    reservation_id: int,
    room_id: int,
) -> dict[str, Any]:
    _ensure_modules_loaded_for_reception()
    status = _get_reservation_status(reservation_id)
    created_events: list[str] = []

    if status == "confirmed":
        _prepare_reception_demo_room(room_id)
        reception_service.check_in_reservation(reservation_id)
        created_events.append("check_in_completed")
        status = _get_reservation_status(reservation_id)

    if status == "checked_in":
        reception_service.check_out_reservation(reservation_id)
        created_events.append("check_out_completed")

    return {
        "reservation_id": reservation_id,
        "created_events": created_events,
        "status": _get_reservation_status(reservation_id),
    }


def _seed_base_records() -> SeedSummary:
    guests: dict[str, int] = {}
    rooms: dict[str, int] = {}
    reservations: dict[str, int] = {}
    billing_accounts: dict[str, dict[str, int]] = {}

    with get_connection() as connection:
        connection.execute("BEGIN")

        try:
            for guest_data in DEMO_GUESTS:
                guests[guest_data["guest_code"]] = _ensure_guest(
                    connection,
                    guest_data,
                )

            for room_data in DEMO_ROOMS:
                rooms[room_data["room_number"]] = _ensure_room(
                    connection,
                    room_data,
                )

            for reservation_data in DEMO_RESERVATIONS:
                reservations[reservation_data["reservation_code"]] = (
                    _ensure_reservation(
                        connection,
                        reservation_data,
                        guests,
                        rooms,
                    )
                )

            first_account_id = _ensure_billing_account(
                connection,
                reservations["CERESA-DEMO-RES-001"],
            )
            _ensure_charge(
                connection,
                first_account_id,
                "CERESA-DEMO settled accommodation",
                50000,
            )
            _ensure_payment(
                connection,
                first_account_id,
                "CERESA-DEMO-PAY-001",
                50000,
            )

            second_account_id = _ensure_billing_account(
                connection,
                reservations["CERESA-DEMO-RES-002"],
            )
            _ensure_charge(
                connection,
                second_account_id,
                "CERESA-DEMO open balance accommodation",
                75000,
            )
            _ensure_payment(
                connection,
                second_account_id,
                "CERESA-DEMO-PAY-002",
                25000,
            )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

    billing_accounts["CERESA-DEMO-RES-001"] = _get_billing_summary(
        first_account_id,
    )
    billing_accounts["CERESA-DEMO-RES-002"] = _get_billing_summary(
        second_account_id,
    )

    return SeedSummary(
        guests=guests,
        rooms=rooms,
        reservations=reservations,
        billing_accounts=billing_accounts,
        audit={},
    )


def _get_billing_summary(billing_account_id: int) -> dict[str, int]:
    account = billing_repository.get_billing_account_by_id(
        billing_account_id,
    )

    if account is None:
        raise RuntimeError("Demo billing account was not found.")

    return {
        "account_id": int(account["id"]),
        "balance_cents": int(account["balance_cents"]),
    }


def seed_demo() -> SeedSummary:
    """Creates or reuses CERESA demo data in the active local database."""
    initialize_database()
    summary = _seed_base_records()

    summary.audit = _create_reception_audit_if_possible(
        summary.reservations["CERESA-DEMO-RES-001"],
        summary.rooms["CERESA-DEMO-D101"],
    )
    summary.billing_accounts["CERESA-DEMO-RES-001"] = (
        _get_billing_summary(
            summary.billing_accounts["CERESA-DEMO-RES-001"]["account_id"],
        )
    )

    return summary


def format_summary(summary: SeedSummary) -> str:
    """Formats seed output for local manual testing."""
    lines = ["CERESA demo seed completed.", "Guests:"]

    for guest_code, guest_id in summary.guests.items():
        lines.append(f"- {guest_code} -> guest_id {guest_id}")

    lines.append("Rooms:")
    for room_number, room_id in summary.rooms.items():
        lines.append(f"- {room_number} -> room_id {room_id}")

    lines.append("Reservations:")
    for reservation_code, reservation_id in summary.reservations.items():
        lines.append(f"- {reservation_code} -> reservation_id {reservation_id}")

    lines.append("Billing:")
    for reservation_code, account in summary.billing_accounts.items():
        lines.append(
            "- "
            f"{reservation_code}: account_id {account['account_id']} "
            f"-> balance {account['balance_cents']}"
        )

    lines.append("Audit:")
    lines.append(
        "- "
        f"reservation_id {summary.audit['reservation_id']} "
        f"status {summary.audit['status']} "
        f"events {summary.audit['created_events']}"
    )

    lines.extend(
        [
            "Useful manual test IDs:",
            "- reservation_id for Reception MVP: "
            f"{summary.reservations['CERESA-DEMO-RES-002']}",
            "- billing_account_id for Billing: "
            f"{summary.billing_accounts['CERESA-DEMO-RES-002']['account_id']}",
            "- reservation_id for Audit: "
            f"{summary.reservations['CERESA-DEMO-RES-001']}",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    """Runs the local development seed and prints a concise summary."""
    print(format_summary(seed_demo()))


if __name__ == "__main__":
    main()
