$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..\frontend")
if (!(Test-Path "node_modules")) { throw "Run .\scripts\install_frontend.ps1 first" }
npm run dev
