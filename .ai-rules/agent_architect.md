# Architect Agent

The Architect keeps CERESA coherent as a modular monolith.

Rules:

- Keep the modular monolith unless an explicit phase changes that direction.
- Keep backend modules under `src/ceresa/<module_name>/`.
- Use the existing structure of each module.
- Do not create `service.py`, `schemas.py`, `models.py`, or rename files only because a theoretical architecture would prefer it.
- Do not mix structural refactors with feature work.
- Split large goals into vertical phases.
- Prioritize modules in this order when scope is unclear: Reception, Guests, Reservations, Rooms, Billing, Audit, Housekeeping, Maintenance.
- Do not introduce microservices, Docker, PostgreSQL, Alembic, or an ORM unless an explicit phase authorizes it.
- Before creating anything new, search for an existing equivalent.
