@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  py -3 -m venv .venv
  if errorlevel 1 exit /b 1
)
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -e .
if errorlevel 1 exit /b 1
start "" http://127.0.0.1:8766/docs
.venv\Scripts\python.exe -m mojo_agent.cli
