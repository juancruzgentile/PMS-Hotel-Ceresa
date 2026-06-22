import sqlite3
from typing import Any
from sqlite3 import Connection

from ceresa.db import get_connection


def list_departments() -> list[dict[str, Any]]:
    """
    Returns all departments ordered by name.
    """
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                code,
                name,
                is_active,
                created_at,
                updated_at
            FROM departments
            ORDER BY name
            """
        ).fetchall()

    return [dict(row) for row in rows]


def get_department_by_id(department_id: int) -> dict[str, Any] | None:
    """
    Returns one department or None when it does not exist.
    """
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                id,
                code,
                name,
                is_active,
                created_at,
                updated_at
            FROM departments
            WHERE id = ?
            """,
            (department_id,),
        ).fetchone()

    return dict(row) if row else None


def get_user_by_id_with_connection(
    connection: Connection,
    user_id: int,
) -> dict[str, Any] | None:
    """
    Returns one user using an existing transaction.
    """
    row = connection.execute(
        """
        SELECT
            users.id,
            users.username,
            users.full_name,
            users.email,
            users.user_type,
            users.department_id,
            departments.code AS department_code,
            departments.name AS department_name,
            users.is_active,
            users.created_at,
            users.updated_at
        FROM users
        LEFT JOIN departments
            ON departments.id = users.department_id
        WHERE users.id = ?
        """,
        (user_id,),
    ).fetchone()

    return dict(row) if row else None


def create_department(code: str, name: str) -> int:
    """
    Creates a department and returns its ID.
    """
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO departments (
                code,
                name
            )
            VALUES (?, ?)
            """,
            (code, name),
        )
        connection.commit()

    return int(cursor.lastrowid)


def create_user(user_data: dict[str, Any]) -> int:
    """
    Creates a user and returns its ID.
    """
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO users (
                username,
                full_name,
                email,
                user_type,
                department_id
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_data["username"],
                user_data["full_name"],
                user_data.get("email"),
                user_data["user_type"],
                user_data.get("department_id"),
            ),
        )
        connection.commit()

    return int(cursor.lastrowid)


def list_users() -> list[dict[str, Any]]:
    """
    Returns users with their department information.
    """
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                users.id,
                users.username,
                users.full_name,
                users.email,
                users.user_type,
                users.department_id,
                departments.code AS department_code,
                departments.name AS department_name,
                users.is_active,
                users.created_at,
                users.updated_at
            FROM users
            LEFT JOIN departments
                ON departments.id = users.department_id
            ORDER BY users.full_name
            """
        ).fetchall()

    return [dict(row) for row in rows]


def is_unique_constraint_error(error: Exception) -> bool:
    """
    Returns True when SQLite reports a duplicate unique value.
    """
    return isinstance(error, sqlite3.IntegrityError) and (
        "UNIQUE constraint failed" in str(error)
    )
