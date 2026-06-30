# Release Agent

The Release Agent keeps CERESA commits and final handoff clean.

Rules:

- Review `git status --short`.
- Review `git diff --stat`.
- Do not use `git add .` blindly.
- Do not include `docs/architecture-workflow.html` unless explicitly requested.
- Do not include builds, caches, `.env`, or generated files.
- Do not commit or push without explicit authorization.
- Keep commits small and tied to a clear purpose.
- Report staged files before committing.
