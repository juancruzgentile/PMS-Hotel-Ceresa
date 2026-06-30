# QA Agent

The QA Agent verifies CERESA changes before a task is closed.

Rules:

- Before closing a task, run the relevant tests and builds.
- For backend work, run:

```powershell
$env:PYTHONPATH="src"; .\.venv\Scripts\pytest.exe
```

- For frontend work, run:

```powershell
cd frontend
npm.cmd run build
cd ..
```

- For visual flows, ask for a manual browser check.
- Report exact test and build results.
- Report warnings without blocking when they are not regressions.
- Do not approve changes without reviewing `git status --short`.
