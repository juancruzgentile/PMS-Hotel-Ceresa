@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo ERROR: Python virtual environment not found at .venv\Scripts\python.exe
  echo Create or activate the CERESA virtual environment before running this script.
  pause
  exit /b 1
)

if not exist "frontend\package.json" (
  echo ERROR: frontend\package.json not found.
  echo Make sure the CERESA frontend exists before running this script.
  pause
  exit /b 1
)

start "CERESA API" cmd /k "cd /d %~dp0 && set PYTHONPATH=src && .venv\Scripts\python.exe -m uvicorn ceresa.main:app --reload --app-dir src --host 127.0.0.1 --port 8000"

start "CERESA Frontend" cmd /k "cd /d %~dp0frontend && npm.cmd run dev"

echo CERESA dev servers are starting.
echo API docs: http://127.0.0.1:8000/docs
echo Frontend: check the Vite terminal window. Usually http://localhost:5173 or http://localhost:5174
echo.
echo Close the opened terminal windows to stop the servers.
endlocal
