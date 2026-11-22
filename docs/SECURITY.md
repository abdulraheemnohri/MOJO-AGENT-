# Security

- API binds to 127.0.0.1 by default.
- Do not expose publicly without authentication, TLS and explicit configuration.
- Tools are allowlisted; arbitrary shell execution is intentionally absent.
- Calculator accepts numeric AST arithmetic only.
- Tool calls require approval by default.
- Evolution optimizes bounded parameters, never source or protected control code.
- Candidate activation requires tests and explicit approval.
- Keep secrets out of source control.
