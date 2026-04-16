# Infra

Infrastructure and environment assets for local development and deployment packaging.

- `docker/`: local compose and service container definitions
- `postgres/`: database bootstrap and initialization assets
- `redis/`: queue and cache service definitions
- `monitoring/`: metrics, tracing, logging, and alerting starter assets
- `environments/`: environment-specific configuration notes and templates

Keep infrastructure definitions operational, minimal, and environment-safe.

Environment templates separate non-sensitive runtime defaults from secret placeholders. Start with `environments/local.env.example` for local development and use `environments/secrets.env.example` only as a checklist for values that must be provided through a secret manager in shared environments.

Local Docker development is defined in `docker/compose.local.yml`. Run it from the repository root with:

```powershell
docker compose -f infra/docker/compose.local.yml up --build
```
