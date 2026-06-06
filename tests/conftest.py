import os

os.environ["CERESA_DATABASE_PATH"] = "data/ceresa_test.db"

import pytest
from fastapi.testclient import TestClient

from ceresa.db import get_connection, initialize_database
from ceresa.main import app


@pytest.fixture
def client() -> TestClient:
    """
    Provides a FastAPI test client.
    """
    return TestClient(app)


@pytest.fixture
def reset_test_data() -> None:
    """
    Cleans test rooms before each test.

    Only rooms starting with TEST- are deleted.
    Real local rooms like 101, 102, 201 are not touched.
    """
    initialize_database()

    with get_connection() as connection:
        connection.execute("DELETE FROM users WHERE username LIKE 'test_%'")
        connection.execute("DELETE FROM departments WHERE code LIKE 'test_%'")
        connection.execute("DELETE FROM rooms WHERE room_number LIKE 'TEST-%'")
        connection.commit()