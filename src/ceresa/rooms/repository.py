from ceresa.db import get_connection


def create_room(room_data: dict) -> int:
    """
    Inserts a new room into the database and returns its ID.
    """
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO rooms (
                room_number,
                floor,
                room_type,
                has_jacuzzi,
                has_balcony,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                room_data["room_number"],
                room_data["floor"],
                room_data["room_type"],
                int(room_data["has_jacuzzi"]),
                int(room_data["has_balcony"]),
                room_data["notes"],
            ),
        )
        connection.commit()
        return cursor.lastrowid


def list_rooms() -> list[dict]:
    """
    Returns all rooms ordered by floor and room number.
    """
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                room_number,
                floor,
                room_type,
                room_status,
                cleaning_status,
                maintenance_status,
                has_jacuzzi,
                has_balcony,
                notes,
                created_at,
                updated_at
            FROM rooms
            ORDER BY floor, room_number
            """
        ).fetchall()

    return [dict(row) for row in rows]


def get_room_by_id(room_id: int) -> dict | None:
    """
    Returns one room by ID.
    If the room does not exist, returns None.
    """
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                id,
                room_number,
                floor,
                room_type,
                room_status,
                cleaning_status,
                maintenance_status,
                has_jacuzzi,
                has_balcony,
                notes,
                created_at,
                updated_at
            FROM rooms
            WHERE id = ?
            """,
            (room_id,),
        ).fetchone()

    if row is None:
        return None

    return dict(row)


def update_room_status(
    room_id: int,
    room_status: str | None,
    cleaning_status: str | None,
    maintenance_status: str | None,
) -> bool:
    """
    Updates room status fields.
    Returns True if the room exists and was updated.
    Returns False if the room does not exist.
    """
    current_room = get_room_by_id(room_id)

    if current_room is None:
        return False

    new_room_status = room_status or current_room["room_status"]
    new_cleaning_status = cleaning_status or current_room["cleaning_status"]
    new_maintenance_status = maintenance_status or current_room["maintenance_status"]

    with get_connection() as connection:
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
                new_room_status,
                new_cleaning_status,
                new_maintenance_status,
                room_id,
            ),
        )
        connection.commit()

    return True


def delete_room(room_id: int) -> bool:
    """
    Deletes a room by ID.
    Returns True if the room existed and was deleted.
    Returns False if the room did not exist.
    """
    existing_room = get_room_by_id(room_id)

    if existing_room is None:
        return False

    with get_connection() as connection:
        connection.execute("DELETE FROM rooms WHERE id = ?", (room_id,))
        connection.commit()

    return True


def list_dirty_rooms() -> list[dict]:
    """
    Returns all rooms with cleaning_status = 'dirty'.
    Used by the housekeeping sector.
    """
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                room_number,
                floor,
                room_type,
                room_status,
                cleaning_status,
                maintenance_status,
                has_jacuzzi,
                has_balcony,
                notes,
                created_at,
                updated_at
            FROM rooms
            WHERE cleaning_status = 'dirty'
            ORDER BY floor, room_number
            """
        ).fetchall()

    return [dict(row) for row in rows]

def list_rooms_needing_repair() -> list[dict]:
    """
    Returns all rooms with maintenance_status = 'needs_repair'.
    Used by the maintenance sector.
    """
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                room_number,
                floor,
                room_type,
                room_status,
                cleaning_status,
                maintenance_status,
                has_jacuzzi,
                has_balcony,
                notes,
                created_at,
                updated_at
            FROM rooms
            WHERE maintenance_status = 'needs_repair'
            ORDER BY floor, room_number
            """
        ).fetchall()

    return [dict(row) for row in rows]

def list_rooms_needing_repair() -> list[dict]:
    """
    Returns all rooms with maintenance_status = 'needs_repair'.
    Used by the maintenance sector.
    """
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                room_number,
                floor,
                room_type,
                room_status,
                cleaning_status,
                maintenance_status,
                has_jacuzzi,
                has_balcony,
                notes,
                created_at,
                updated_at
            FROM rooms
            WHERE maintenance_status = 'needs_repair'
            ORDER BY floor, room_number
            """
        ).fetchall()

    return [dict(row) for row in rows]