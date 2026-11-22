# MOJO AGENT 0.4 implementation notes

- Memory export: GET /api/v1/memory/export.
- Memory import: POST /api/v1/memory/import using format mojo-memory-v1.
- Import is additive, validates each item using normal memory rules, and accepts up to 5,000 entries per request.
- Theme supports dark, light, and system. Tool approval is a protected invariant and cannot be disabled.
- API host and port are launch-time settings. The API binds to loopback by default.
- Evolution candidates and approvals are still process-local and reset after a backend restart.
- No arbitrary shell execution or source self-modification is enabled.
- Keep exported memory backups private; they may contain sensitive personal content.
