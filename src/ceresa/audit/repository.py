from sqlite3 import Connection
from typing import Any

from ceresa.db import get_connection


def create_audit_event_with_connection(
    connection: Connection,
    event_data: dict[str, Any],
) -> int:
    """
    Creates an audit event using an existing transaction.
    """
    cursor = connection.execute(
        """
        INSERT INTO audit_events (
            module,
            event_type,
            entity_type,
            entity_id,
            reservation_id,
            room_id,
            billing_account_id,
            actor_user_id,
            before_state_json,
            after_state_json,
            metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_data["module"],
            event_data["event_type"],
            event_data["entity_type"],
            event_data["entity_id"],
            event_data.get("reservation_id"),
            event_data.get("room_id"),
            event_data.get("billing_account_id"),
            event_data.get("actor_user_id"),
            event_data.get("before_state_json"),
            event_data.get("after_state_json"),
            event_data.get("metadata_json"),
        ),
    )

    return int(cursor.lastrowid)


def list_audit_events_by_reservation_id(
    reservation_id: int,
) -> list[dict[str, Any]]:
    """
    Lists audit events for one reservation in creation order.
    """
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                module,
                event_type,
                entity_type,
                entity_id,
                reservation_id,
                room_id,
                billing_account_id,
                actor_user_id,
                before_state_json,
                after_state_json,
                metadata_json,
                created_at
            FROM audit_events
            WHERE reservation_id = ?
            ORDER BY id
            """,
            (reservation_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def get_audit_event_by_id(event_id: int) -> dict[str, Any] | None:
    """
    Returns one audit event by ID.
    """
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                id,
                module,
                event_type,
                entity_type,
                entity_id,
                reservation_id,
                room_id,
                billing_account_id,
                actor_user_id,
                before_state_json,
                after_state_json,
                metadata_json,
                created_at
            FROM audit_events
            WHERE id = ?
            """,
            (event_id,),
        ).fetchone()

    return dict(row) if row else None
