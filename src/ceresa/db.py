from pathlib import Path
import os
import sqlite3


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DEFAULT_DATABASE_PATH = DATA_DIR / "ceresa.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def get_database_path() -> Path:
    """
    Returns the active database path.

    By default Ceresa uses:
    data/ceresa.db

    During tests we can override it using:
    CERESA_DATABASE_PATH=data/ceresa_test.db
    """
    custom_database_path = os.getenv("CERESA_DATABASE_PATH")

    if custom_database_path:
        return Path(custom_database_path)

    return DEFAULT_DATABASE_PATH


def get_connection() -> sqlite3.Connection:
    """
    Creates and returns a SQLite connection.

    Important:
    - row_factory lets us read rows like dictionaries.
    - PRAGMA foreign_keys = ON protects relational integrity.
    """
    DATA_DIR.mkdir(exist_ok=True)

    database_path = get_database_path()
    database_path.parent.mkdir(exist_ok=True)

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")

    return connection


def initialize_database() -> None:
    """
    Creates the database structure if it does not already exist.
    """
    with get_connection() as connection:
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        connection.executescript(schema_sql)
        connection.commit()