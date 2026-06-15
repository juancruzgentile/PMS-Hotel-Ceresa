import sqlite3
from typing import Any

from ceresa.db import get_connection


def create_guest(guest_data: dict[str, Any]) -> int:
    """
    Creates a guest profile and returns its database ID.
    """
    with get_connection() as connection:
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
        connection.commit()

    return int(cursor.lastrowid)


def list_guests() -> list[dict[str, Any]]:
    """
    Returns all guest profiles ordered by last name and first name.
    """
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                guest_code,
                first_name,
                last_name,
                email,
                phone,
                nationality,
                notes,
                is_active,
                created_at,
                updated_at
            FROM guests
            ORDER BY last_name, first_name
            """
        ).fetchall()

    return [dict(row) for row in rows]


def get_guest_by_id(guest_id: int) -> dict[str, Any] | None:
    """
    Returns one guest profile or None when it does not exist.
    """
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                id,
                guest_code,
                first_name,
                last_name,
                email,
                phone,
                nationality,
                notes,
                is_active,
                created_at,
                updated_at
            FROM guests
            WHERE id = ?
            """,
            (guest_id,),
        ).fetchone()

    return dict(row) if row else None


def is_unique_constraint_error(error: Exception) -> bool:
    """
    Detects duplicate guest codes reported by SQLite.
    """
    return isinstance(error, sqlite3.IntegrityError) and (
        "UNIQUE constraint failed" in str(error)
    )