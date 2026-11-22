$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
if (!(Test-Path ".venv\Scripts\mojo-agent.exe")) { throw "Run .\scripts\install_backend.ps1 first" }
& .\.venv\Scripts\mojo-agent.exe @args
