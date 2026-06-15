import os

# Must be configured before importing Ceresa modules.
os.environ["CERESA_DATABASE_PATH"] = "data/ceresa_test.db"

import pytest
from fastapi.testclient import TestClient

from ceresa.db import get_connection, initialize_database
from ceresa.main import app


@pytest.fixture
def client():
    """
    Provides a FastAPI test client and executes the app lifespan.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def reset_test_data() -> None:
    """
    Initializes and cleans the dedicated test database before a test.

    Child records must be deleted before their parent records
    because SQLite foreign-key protection is enabled.
    """
    initialize_database()

    with get_connection() as connection:
        connection.execute("DELETE FROM billing_payments")
        connection.execute("DELETE FROM billing_charges")
        connection.execute("DELETE FROM billing_accounts")

        connection.execute("DELETE FROM reservations")
        connection.execute("DELETE FROM guests")

        connection.execute("DELETE FROM users")
        connection.execute("DELETE FROM departments")

        connection.execute("DELETE FROM rooms")

        connection.execute(
            """
            DELETE FROM sqlite_sequence
            WHERE name IN (
                'billing_payments',
                'billing_charges',
                'billing_accounts',
                'reservations',
                'guests',
                'users',
                'departments',
                'rooms'
            )
            """
        )

        connection.commit()