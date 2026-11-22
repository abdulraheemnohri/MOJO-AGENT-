$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv/Scripts/python.exe"
if (-not (Test-Path $Python)) { throw "Run .\scripts\install_backend.ps1 first." }
& $Python -m pip install --upgrade litert-lm
if ($LASTEXITCODE -ne 0) { throw "LiteRT-LM installation failed" }
& $Python -m mojo_agent.cli litertlm status
