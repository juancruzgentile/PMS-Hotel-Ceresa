# Backend Agent

The Backend Agent keeps CERESA backend work aligned with the current FastAPI and direct SQLite architecture.

Rules:

- Use the current FastAPI application.
- Use existing `routes.py`, repositories, and services when they exist.
- Do not introduce Flask.
- Do not introduce SQLAlchemy, SQLModel, or any ORM in Phase 1.
- Keep direct SQLite access.
- Use Pydantic in endpoints when appropriate.
- Keep rollback and transaction handling for critical operations.
- Add or update tests when backend behavior is changed.
- Run backend tests with:

```powershell
$env:PYTHONPATH="src"; .\.venv\Scripts\pytest.exe
```

- Do not trust global `pytest`; use the project virtual environment.
