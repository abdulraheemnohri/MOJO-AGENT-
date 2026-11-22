$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..\frontend")
if (!(Get-Command npm -ErrorAction SilentlyContinue)) { throw "Node.js 20+ and npm are required" }
npm install
npm run build
Write-Host "Frontend installed and production build verified."
