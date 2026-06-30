# CERESA Phase 2 Roadmap

This document is a roadmap for future planning. It is not an implementation plan for the current phase.

## 1. Objective of Phase 2

Phase 2 should prepare CERESA for more reliable development, deployment, and operational growth while preserving the modular monolith until a dedicated phase authorizes deeper infrastructure changes.

The focus should be on decisions, evaluation criteria, and small preparation steps that reduce future risk without changing the current stack prematurely.

## 2. Docker as a Future Option

Docker may be evaluated later to standardize local development and deployment environments.

Before adoption, the project should define which services need containers, how local SQLite data is handled, and whether the added complexity helps the team.

## 3. PostgreSQL as a Future Option

PostgreSQL may be evaluated later if CERESA needs stronger production database capabilities, concurrent access patterns, operational tooling, or deployment compatibility.

SQLite remains the current persistence layer until an explicit migration phase is approved.

## 4. Versioned Migrations as a Future Option

Versioned migrations may be evaluated when schema changes become frequent enough to require controlled upgrade paths.

Any migration tool should be chosen after reviewing the current schema, test strategy, deployment needs, and rollback expectations.

## 5. Future ORM Evaluation

An ORM may be evaluated in the future, but no ORM has been selected definitively.

The decision should compare direct SQLite access with alternatives based on maintainability, transaction control, testability, migration support, and the learning cost for the project.

## 6. Real Auth as Phase 3, Not Phase 2

Real authentication is a Phase 3 concern, not a Phase 2 goal.

`actor_user_id` remains manual traceability until an explicit authentication phase introduces login, sessions, roles, permissions, or token-based flows.

## 7. Future Deploy

Deployment options should be evaluated later based on cost, reliability, operational limits, backups, environment management, and support for the chosen database.

No provider should be assumed to be free or selected without future verification.

## 8. Pending Decisions Before Adoption

Before adopting Docker, PostgreSQL, migrations, an ORM, or deployment infrastructure, CERESA should decide:

- Which hotel workflows are stable enough to justify infrastructure changes.
- Whether the modular monolith remains the right boundary.
- How backups, restores, and data migration will work.
- Which environments are required: local, staging, and production.
- Which commands developers must run consistently on Windows.
- Which tests must pass before infrastructure changes are accepted.
- How secrets and environment variables will be managed without committing real `.env` files.

## 9. Criteria to Start Phase 2

Phase 2 can start when:

- Phase 1 MVP flows are stable enough for broader testing.
- Backend and frontend test/build commands are consistently passing.
- The team agrees on the specific operational problem Phase 2 should solve.
- The project has a documented migration and rollback expectation for any persistence change.
- The scope is limited to roadmap-approved infrastructure work, not real auth or unrelated feature expansion.
