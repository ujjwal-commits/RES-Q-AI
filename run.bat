@echo off
title RESQ-AI
cd /d "%~dp0"

set "PY=python"
where python >nul 2>nul || set "PY=py"
where %PY% >nul 2>nul
if errorlevel 1 (
  echo Python was not found.
  echo Install Python 3 from python.org, tick "Add Python to PATH", then double-click run.bat again.
  pause
  exit /b 1
)

%PY% -c "import pandas, sklearn" >nul 2>nul
if errorlevel 1 (
  echo First run: installing pandas and scikit-learn. This needs internet only this once.
  %PY% -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Install failed. Check your internet connection and try again.
    pause
    exit /b 1
  )
)

%PY% server.py
pause
