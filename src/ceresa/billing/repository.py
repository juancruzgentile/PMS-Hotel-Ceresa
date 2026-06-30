import sqlite3
from sqlite3 import Connection
from typing import Any

from ceresa.db import get_connection


def _build_billing_account_from_connection(
    connection: Connection,
    billing_account_id: int,
) -> dict[str, Any] | None:
    account_row = connection.execute(
        """
        SELECT
            billing_accounts.id,
            billing_accounts.reservation_id,
            reservations.reservation_code,
            reservations.guest_id,
            guests.guest_code,
            guests.first_name AS guest_first_name,
            guests.last_name AS guest_last_name,
            reservations.room_id,
            rooms.room_number,
            billing_accounts.status,
            billing_accounts.notes,
            billing_accounts.created_at,
            billing_accounts.updated_at
        FROM billing_accounts
        INNER JOIN reservations
            ON reservations.id = billing_accounts.reservation_id
        INNER JOIN guests
            ON guests.id = reservations.guest_id
        INNER JOIN rooms
            ON rooms.id = reservations.room_id
        WHERE billing_accounts.id = ?
        """,
        (billing_account_id,),
    ).fetchone()

    if account_row is None:
        return None

    charge_rows = connection.execute(
        """
        SELECT
            id,
            source_module,
            description,
            amount_cents,
            created_at
        FROM billing_charges
        WHERE billing_account_id = ?
        ORDER BY id
        """,
        (billing_account_id,),
    ).fetchall()

    payment_rows = connection.execute(
        """
        SELECT
            id,
            payment_method,
            amount_cents,
            reference,
            created_at
        FROM billing_payments
        WHERE billing_account_id = ?
        ORDER BY id
        """,
        (billing_account_id,),
    ).fetchall()

    account = dict(account_row)
    charges = [dict(row) for row in charge_rows]
    payments = [dict(row) for row in payment_rows]

    charges_total_cents = sum(
        charge["amount_cents"] for charge in charges
    )
    payments_total_cents = sum(
        payment["amount_cents"] for payment in payments
    )

    account["charges"] = charges
    account["payments"] = payments
    account["charges_total_cents"] = charges_total_cents
    account["payments_total_cents"] = payments_total_cents
    account["balance_cents"] = (
        charges_total_cents - payments_total_cents
    )

    return account


def create_billing_account_with_connection(
    connection: Connection,
    reservation_id: int,
    notes: str | None,
) -> int:
    """
    Creates a billing account inside an existing transaction.
    """
    cursor = connection.execute(
        """
        INSERT INTO billing_accounts (
            reservation_id,
            notes
        )
        VALUES (?, ?)
        """,
        (
            reservation_id,
            notes,
        ),
    )

    return int(cursor.lastrowid)


def get_billing_account_by_id_with_connection(
    connection: Connection,
    billing_account_id: int,
) -> dict[str, Any] | None:
    """
    Returns a billing account using an existing transaction.
    """
    return _build_billing_account_from_connection(
        connection,
        billing_account_id,
    )


def get_billing_account_by_reservation_id_with_connection(
    connection: Connection,
    reservation_id: int,
) -> dict[str, Any] | None:
    """
    Returns one reservation billing account in an existing transaction.
    """
    row = connection.execute(
        """
        SELECT id
        FROM billing_accounts
        WHERE reservation_id = ?
        """,
        (reservation_id,),
    ).fetchone()

    if row is None:
        return None

    return get_billing_account_by_id_with_connection(
        connection,
        int(row["id"]),
    )


def close_billing_account_with_connection(
    connection: Connection,
    billing_account_id: int,
) -> None:
    """
    Closes a billing account inside an existing transaction.
    """
    connection.execute(
        """
        UPDATE billing_accounts
        SET
            status = 'closed',
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (billing_account_id,),
    )


def reservation_is_billable(reservation_id: int) -> bool:
    """
    Returns True when the reservation exists and is not cancelled.
    """
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id
            FROM reservations
            WHERE id = ?
              AND status != 'cancelled'
            """,
            (reservation_id,),
        ).fetchone()

    return row is not None


def create_billing_account(
    reservation_id: int,
    notes: str | None,
) -> int:
    """
    Creates a billing account for one reservation.
    """
    with get_connection() as connection:
        account_id = create_billing_account_with_connection(
            connection,
            reservation_id,
            notes,
        )
        connection.commit()

    return account_id


def list_billing_accounts() -> list[dict[str, Any]]:
    """
    Lists billing accounts with operational summary data.
    """
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                billing_accounts.id AS billing_account_id,
                billing_accounts.reservation_id,
                reservations.reservation_code,
                guests.first_name AS guest_first_name,
                guests.last_name AS guest_last_name,
                rooms.room_number,
                billing_accounts.status,
                billing_accounts.created_at,
                billing_accounts.updated_at,
                COALESCE(charges.total_charges_cents, 0)
                    AS total_charges_cents,
                COALESCE(payments.total_payments_cents, 0)
                    AS total_payments_cents,
                COALESCE(charges.total_charges_cents, 0)
                    - COALESCE(payments.total_payments_cents, 0)
                    AS balance_cents
            FROM billing_accounts
            INNER JOIN reservations
                ON reservations.id = billing_accounts.reservation_id
            INNER JOIN guests
                ON guests.id = reservations.guest_id
            INNER JOIN rooms
                ON rooms.id = reservations.room_id
            LEFT JOIN (
                SELECT
                    billing_account_id,
                    SUM(amount_cents) AS total_charges_cents
                FROM billing_charges
                GROUP BY billing_account_id
            ) AS charges
                ON charges.billing_account_id = billing_accounts.id
            LEFT JOIN (
                SELECT
                    billing_account_id,
                    SUM(amount_cents) AS total_payments_cents
                FROM billing_payments
                GROUP BY billing_account_id
            ) AS payments
                ON payments.billing_account_id = billing_accounts.id
            ORDER BY billing_accounts.id DESC
            """
        ).fetchall()

    accounts = [dict(row) for row in rows]

    for account in accounts:
        account["guest_name"] = (
            f"{account['guest_first_name']} "
            f"{account['guest_last_name']}"
        )

    return accounts


def create_charge(
    billing_account_id: int,
    charge_data: dict[str, Any],
) -> int:
    """
    Adds a positive charge to a billing account.
    """
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO billing_charges (
                billing_account_id,
                source_module,
                description,
                amount_cents
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                billing_account_id,
                charge_data["source_module"],
                charge_data["description"],
                charge_data["amount_cents"],
            ),
        )
        connection.commit()

    return int(cursor.lastrowid)


def create_payment(
    billing_account_id: int,
    payment_data: dict[str, Any],
) -> int:
    """
    Adds a payment to a billing account.
    """
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO billing_payments (
                billing_account_id,
                payment_method,
                amount_cents,
                reference
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                billing_account_id,
                payment_data["payment_method"],
                payment_data["amount_cents"],
                payment_data.get("reference"),
            ),
        )
        connection.commit()

    return int(cursor.lastrowid)


def get_billing_account_by_id(
    billing_account_id: int,
) -> dict[str, Any] | None:
    """
    Returns a billing account with reservation, guest,
    room, charges, payments and calculated balance.
    """
    with get_connection() as connection:
        return get_billing_account_by_id_with_connection(
            connection,
            billing_account_id,
        )


def get_billing_account_by_reservation_id(
    reservation_id: int,
) -> dict[str, Any] | None:
    """
    Returns the billing account associated with one reservation.
    """
    with get_connection() as connection:
        return get_billing_account_by_reservation_id_with_connection(
            connection,
            reservation_id,
        )


def is_unique_constraint_error(error: Exception) -> bool:
    """
    Detects duplicate billing accounts reported by SQLite.
    """
    return isinstance(error, sqlite3.IntegrityError) and (
        "UNIQUE constraint failed" in str(error)
    )
