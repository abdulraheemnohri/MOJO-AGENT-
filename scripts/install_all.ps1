$ErrorActionPreference = "Stop"
& (Join-Path $PSScriptRoot "install_backend.ps1")
& (Join-Path $PSScriptRoot "install_frontend.ps1")
