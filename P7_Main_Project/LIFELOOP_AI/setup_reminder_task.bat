@echo off
setlocal
set "APP_DIR=%~dp0"
set "PY=%APP_DIR%.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

echo Creating LIFELOOP daily deadline reminder task...
schtasks /Create /TN "LIFELOOP Deadline Reminder" /TR "\"%PY%\" \"%APP_DIR%reminder_worker.py\"" /SC DAILY /ST 09:00 /F
if errorlevel 1 (
  echo Failed. Run this file as Administrator, or create the task manually in Windows Task Scheduler.
) else (
  echo Done. LIFELOOP will check deadlines every day at 09:00.
)
pause
