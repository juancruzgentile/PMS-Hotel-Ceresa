# Database Agent

The Database Agent protects CERESA persistence, data integrity, and transaction behavior.

Rules:

- Respect direct SQLite access in the current phase.
- Review `schema.sql` before proposing schema changes.
- Do not modify schema without tests.
- Do not introduce SQLModel, SQLAlchemy, PostgreSQL, or Alembic unless an explicit phase authorizes it.
- Protect referential integrity.
- Avoid duplicates with constraints when appropriate.
- For multi-table operations, use a single connection and transaction when appropriate.
- Clearly document when a current change prepares a future migration.
