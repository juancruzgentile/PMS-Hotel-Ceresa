import sqlite3
from typing import Any
from sqlite3 import Connection

from ceresa.db import get_connection


def get_reservation_by_id_with_connection(
    connection: Connection,
    reservation_id: int,
) -> dict[str, Any] | None:
    """
    Returns one reservation using an existing transaction.
    """
    row = connection.execute(
        """
        SELECT
            reservations.id,
            reservations.reservation_code,
            reservations.guest_id,
            guests.guest_code,
            guests.first_name AS guest_first_name,
            guests.last_name AS guest_last_name,
            reservations.room_id,
            rooms.room_number,
            reservations.check_in_date,
            reservations.check_out_date,
            reservations.status,
            reservations.adults,
            reservations.children,
            reservations.notes,
            reservations.created_at,
            reservations.updated_at
        FROM reservations
        INNER JOIN guests
            ON guests.id = reservations.guest_id
        INNER JOIN rooms
            ON rooms.id = reservations.room_id
        WHERE reservations.id = ?
        """,
        (reservation_id,),
    ).fetchone()

    return dict(row) if row else None


def update_reservation_status_with_connection(
    connection: Connection,
    reservation_id: int,
    status: str,
) -> None:
    """
    Updates one reservation status inside an existing transaction.
    """
    connection.execute(
        """
        UPDATE reservations
        SET
            status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            status,
            reservation_id,
        ),
    )


def guest_exists(guest_id: int) -> bool:
    """
    Returns True when the guest exists and is active.
    """
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id
            FROM guests
            WHERE id = ?
              AND is_active = 1
            """,
            (guest_id,),
        ).fetchone()

    return row is not None


def room_exists(room_id: int) -> bool:
    """
    Returns True when the room exists.
    """
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id
            FROM rooms
            WHERE id = ?
            """,
            (room_id,),
        ).fetchone()

    return row is not None


def room_exists_with_connection(
    connection: Connection,
    room_id: int,
) -> bool:
    """
    Returns True when the room exists using an existing transaction.
    """
    row = connection.execute(
        """
        SELECT id
        FROM rooms
        WHERE id = ?
        """,
        (room_id,),
    ).fetchone()

    return row is not None


def room_has_overlapping_reservation(
    room_id: int,
    check_in_date: str,
    check_out_date: str,
) -> bool:
    """
    Checks whether the room already has an active reservation
    overlapping the requested dates.
    """
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id
            FROM reservations
            WHERE room_id = ?
              AND status IN (
                  'pending',
                  'confirmed',
                  'checked_in'
              )
              AND check_in_date < ?
              AND check_out_date > ?
            LIMIT 1
            """,
            (
                room_id,
                check_out_date,
                check_in_date,
            ),
        ).fetchone()

    return row is not None


def room_has_overlapping_reservation_with_connection(
    connection: Connection,
    room_id: int,
    check_in_date: str,
    check_out_date: str,
    exclude_reservation_id: int | None = None,
) -> bool:
    """
    Checks active room overlaps inside an existing transaction.
    """
    values: list[Any] = [
        room_id,
        check_out_date,
        check_in_date,
    ]
    exclusion_sql = ""

    if exclude_reservation_id is not None:
        exclusion_sql = "AND id != ?"
        values.append(exclude_reservation_id)

    row = connection.execute(
        f"""
        SELECT id
        FROM reservations
        WHERE room_id = ?
          AND status IN (
              'pending',
              'confirmed',
              'checked_in'
          )
          AND check_in_date < ?
          AND check_out_date > ?
          {exclusion_sql}
        LIMIT 1
        """,
        tuple(values),
    ).fetchone()

    return row is not None


def update_reservation_dates_with_connection(
    connection: Connection,
    reservation_id: int,
    check_in_date: str,
    check_out_date: str,
) -> None:
    """
    Updates reservation dates inside an existing transaction.
    """
    connection.execute(
        """
        UPDATE reservations
        SET
            check_in_date = ?,
            check_out_date = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            check_in_date,
            check_out_date,
            reservation_id,
        ),
    )


def update_reservation_room_with_connection(
    connection: Connection,
    reservation_id: int,
    room_id: int,
) -> None:
    """
    Updates reservation room inside an existing transaction.
    """
    connection.execute(
        """
        UPDATE reservations
        SET
            room_id = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            room_id,
            reservation_id,
        ),
    )


def create_reservation(reservation_data: dict[str, Any]) -> int:
    """
    Creates a reservation and returns its database ID.
    """
    with get_connection() as connection:
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
                reservation_data["guest_id"],
                reservation_data["room_id"],
                reservation_data["check_in_date"],
                reservation_data["check_out_date"],
                reservation_data["status"],
                reservation_data["adults"],
                reservation_data["children"],
                reservation_data.get("notes"),
            ),
        )
        connection.commit()

    return int(cursor.lastrowid)


def list_reservations() -> list[dict[str, Any]]:
    """
    Returns reservations with guest and room information.
    """
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                reservations.id,
                reservations.reservation_code,
                reservations.guest_id,
                guests.guest_code,
                guests.first_name AS guest_first_name,
                guests.last_name AS guest_last_name,
                reservations.room_id,
                rooms.room_number,
                reservations.check_in_date,
                reservations.check_out_date,
                reservations.status,
                reservations.adults,
                reservations.children,
                reservations.notes,
                reservations.created_at,
                reservations.updated_at
            FROM reservations
            INNER JOIN guests
                ON guests.id = reservations.guest_id
            INNER JOIN rooms
                ON rooms.id = reservations.room_id
            ORDER BY
                reservations.check_in_date,
                rooms.room_number
            """
        ).fetchall()

    return [dict(row) for row in rows]


def _list_reservations_by_date_column(
    date_column: str,
    target_date: str,
) -> list[dict[str, Any]]:
    """
    Returns non-cancelled reservations matching one reservation date.
    """
    allowed_date_columns = {
        "check_in_date",
        "check_out_date",
    }
    if date_column not in allowed_date_columns:
        raise ValueError("Invalid reservation date column.")

    with get_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT
                reservations.id,
                reservations.reservation_code,
                reservations.guest_id,
                guests.guest_code,
                guests.first_name AS guest_first_name,
                guests.last_name AS guest_last_name,
                reservations.room_id,
                rooms.room_number,
                reservations.check_in_date,
                reservations.check_out_date,
                reservations.status,
                reservations.adults,
                reservations.children,
                reservations.notes,
                reservations.created_at,
                reservations.updated_at
            FROM reservations
            INNER JOIN guests
                ON guests.id = reservations.guest_id
            INNER JOIN rooms
                ON rooms.id = reservations.room_id
            WHERE reservations.{date_column} = ?
              AND reservations.status != 'cancelled'
            ORDER BY
                rooms.room_number,
                reservations.reservation_code
            """,
            (target_date,),
        ).fetchall()

    return [dict(row) for row in rows]


def list_reservations_by_check_in_date(
    check_in_date: str,
) -> list[dict[str, Any]]:
    """
    Returns non-cancelled reservations arriving on one date.
    """
    return _list_reservations_by_date_column(
        "check_in_date",
        check_in_date,
    )


def list_reservations_by_check_out_date(
    check_out_date: str,
) -> list[dict[str, Any]]:
    """
    Returns non-cancelled reservations departing on one date.
    """
    return _list_reservations_by_date_column(
        "check_out_date",
        check_out_date,
    )


def get_reservation_by_id(
    reservation_id: int,
) -> dict[str, Any] | None:
    """
    Returns one reservation with guest and room information.
    """
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                reservations.id,
                reservations.reservation_code,
                reservations.guest_id,
                guests.guest_code,
                guests.first_name AS guest_first_name,
                guests.last_name AS guest_last_name,
                reservations.room_id,
                rooms.room_number,
                reservations.check_in_date,
                reservations.check_out_date,
                reservations.status,
                reservations.adults,
                reservations.children,
                reservations.notes,
                reservations.created_at,
                reservations.updated_at
            FROM reservations
            INNER JOIN guests
                ON guests.id = reservations.guest_id
            INNER JOIN rooms
                ON rooms.id = reservations.room_id
            WHERE reservations.id = ?
            """,
            (reservation_id,),
        ).fetchone()

    return dict(row) if row else None


def is_unique_constraint_error(error: Exception) -> bool:
    """
    Detects duplicated reservation codes.
    """
    return isinstance(error, sqlite3.IntegrityError) and (
        "UNIQUE constraint failed" in str(error)
    )
