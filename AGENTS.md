# CERESA Agent Instructions

## Project identity

CERESA is a modular PMS for hotels. It is currently a modular monolith: modules live together in one application while keeping domain boundaries clear enough to grow independently.

The goal is for modules to evolve in a decoupled way. In the future, some modules may be separated into independent services or packages, but that is roadmap work, not the current architecture.

CERESA must adapt to hotels that do not have every sector, process, or technology. Features should remain modular and optional where the hotel workflow requires it.

## Current architecture

- Backend: Python/FastAPI.
- Persistence: direct SQLite access.
- Tests: pytest.
- Frontend: Vite/React/TypeScript.
- Backend modules live under `src/ceresa/<module_name>/`.
- Tests live under `tests/`.
- Frontend lives under `frontend/`.

## Current known state

- Reception MVP backend + frontend already exists.
- The guest -> reservation -> billing -> payment -> reception -> audit events flow is available as an MVP.
- Transactional audit events already exist.
- Optional `actor_user_id` already exists in Reception audit events.
- `guests`, `rooms`, `reservations`, `billing`, `reception`, `audit`, and `users` already exist.
- `docs/architecture-workflow.html` may exist untracked and must not be included automatically in commits.

## Strategic direction

- Prioritize growth by phases.
- Prefer small, vertical, testable changes.
- Do not make large rewrites without an explicit phase.
- Do not reorganize folders until there is a dedicated refactor phase.
- Keep the modular monolith until domain boundaries are clear.
- Treat module separation or microservices only as future roadmap work.

## Strict prohibitions unless explicitly requested

- No PostgreSQL.
- No Docker.
- No Alembic.
- No SQLAlchemy.
- No Flask.
- No microservices.
- No full authentication, JWT, sessions, or complex permissions without an explicit phase.
- Do not touch `docs/` unless explicitly requested.
- Do not commit or push without explicit authorization.
- Do not use `git reset`, `git clean`, `git restore`, or history rewriting.

## Backend commands

Run backend tests with:

```powershell
$env:PYTHONPATH="src"; .\.venv\Scripts\pytest.exe
```

Run the backend server with:

```powershell
$env:PYTHONPATH="src"; .\.venv\Scripts\python.exe -m uvicorn ceresa.main:app --reload --app-dir src --host 127.0.0.1 --port 8000
```

Do not trust global `pytest`. Always use the project `.venv` from `ceresa`, not the one from `ceresa-agents`.

## Frontend commands

Run the frontend dev server with:

```powershell
cd frontend
npm.cmd run dev
```

Run the frontend build with:

```powershell
cd frontend
npm.cmd run build
```

On Windows, use `npm.cmd` to avoid PowerShell execution policy issues. Do not commit `node_modules`, `dist`, `.vite`, or generated TypeScript/Vite files.

## Workflow for every task

1. Review `git status --short`.
2. Inspect existing files before creating new ones.
3. Avoid duplicating functionality.
4. Change the minimum necessary.
5. Add or update tests when backend is touched.
6. Run the backend suite when backend is touched.
7. Run the frontend build when frontend is touched.
8. Report modified files.
9. Report exact tests/builds run.
10. Report risks.
11. Do not commit or push without authorization.

## AI persona routing

- For complex tasks, consult `.ai-rules/orchestrator.md`.
- For backend work, consult `.ai-rules/agent_backend.md`.
- For data, SQLite, schema, or transactions, consult `.ai-rules/agent_database.md`.
- For frontend work, consult `.ai-rules/agent_frontend.md` and `frontend/AGENTS.md`.
- For users, audit trail, billing, permissions, or sensitive data, consult `.ai-rules/agent_security.md`.
- Before closing a task, consult `.ai-rules/agent_qa.md` and `.ai-rules/agent_release.md`.
- These rules complement `AGENTS.md`; they do not replace it.

## Internal responsibility model

Codex should simulate these roles before and during each task.

### Architect

- Reviews scope, architecture, and risks.
- Decides whether the task should be split.
- Avoids premature jumps to future infrastructure.

### Backend Engineer

- Works in FastAPI, direct SQLite, services, routes, repositories, and tests.
- Maintains transactions and rollback behavior when appropriate.
- Does not introduce ORMs or alternative frameworks.

### Frontend Engineer

- Works in React/Vite/TypeScript.
- Prioritizes functional, clear UI before advanced design.
- Keeps API calls centralized.

### QA Reviewer

- Verifies tests, builds, regressions, and edge cases.
- Requests manual checks when the flow is visual.

### Security and Data Reviewer

- Reviews audit trail, sensitive data, payments, users, and future permissions.
- Must not pretend real authentication exists when only manual/optional `actor_user_id` exists.

### Release Reviewer

- Reviews staged files.
- Avoids including `docs/` or generated files by mistake.
- Does not allow commit or push without explicit authorization.

## Handling large goals

- If the user asks for something large, propose a sequence of phases.
- If implementing a large phase, keep a clear vertical slice.
- Do not mix structural refactor with functionality.
- Do not mix real authentication with UI or Reception improvements unless explicitly requested.

## Repository hygiene

- Keep `.gitignore` updated.
- Do not include caches or generated builds.
- Use small, reviewable commits.
- Report untracked files before adding them.
