$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Test-Path ".venv/Scripts/python.exe")) { py -3 -m venv .venv }
& .venv/Scripts/python.exe -m pip install --upgrade pip
& .venv/Scripts/python.exe -m pip install -e ".[dev]"
if ($LASTEXITCODE -ne 0) { throw "Install failed" }
Write-Host "MOJO AGENT ready. Starting local API at http://127.0.0.1:8766"
Start-Process "http://127.0.0.1:8766/docs"
& .venv/Scripts/python.exe -m mojo_agent.cli
