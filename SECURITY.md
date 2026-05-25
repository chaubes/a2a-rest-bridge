# Security Policy

AgentCart is a demonstration project that accompanies an article on hybrid
REST + A2A architecture. It is **not intended for production use**: payments and
shipping are deterministic mocks, no real money moves, and all data lives in
embedded in-memory H2 databases that reset on restart.

## Reporting a vulnerability

Please report security issues privately through GitHub's
[private vulnerability reporting](https://github.com/chaubes/a2a-rest-bridge/security/advisories/new)
rather than opening a public issue. Reports are acknowledged and addressed on a
best-effort basis.

## Notes for reviewers

- No secrets or credentials are committed. Configuration is supplied through a
  local, git-ignored `.env` file; only `.env.example` (with placeholders) is in
  version control.
- Input validation and guardrails are enforced at the MCP and REST layers — see
  [`docs/guardrails.md`](docs/guardrails.md).
- The language model never reaches a REST API directly; every action passes
  through schema validation and guardrail checks first.
