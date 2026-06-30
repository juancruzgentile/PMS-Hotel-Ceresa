# CERESA AI Rules

This folder contains persona routing rules for Codex inside CERESA.

These files do not execute external agents, do not invoke Ollama, and do not replace `AGENTS.md`. They are operational rules that help Codex classify tasks, apply domain review, and report decisions with clearer responsibility boundaries.

Use these rules to decide which internal review perspective should be active before implementation: architecture, backend, database, frontend, security, QA, or release.

Future technologies must be treated as roadmap options, not immediate implementation. If a task suggests Docker, PostgreSQL, Alembic, ORM adoption, real auth, microservices, or deploy infrastructure, keep it in roadmap language unless an explicit implementation phase authorizes it.
