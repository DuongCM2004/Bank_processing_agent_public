# Backend

Production API service for the Ops Agent MVP.

Expected stack:

- FastAPI for REST endpoints and OpenAPI generation
- SQLAlchemy + Alembic for PostgreSQL persistence
- Pydantic for typed request and response schemas
- Redis/Celery integration points under infrastructure and tasks

Design rules:

- keep routes thin
- keep workflow and decision logic in use cases and services
- keep repository and DB concerns in infrastructure
- make every state transition and audit event explicit

Database migrations:

- Alembic configuration lives under [alembic/README.md](D:/Self_study/computer_science/Personal_project/bank_document_processing_agent/apps/backend/alembic/README.md).
- The backend reads PostgreSQL connection details from `OPS_AGENT_POSTGRES_DSN`.
- Local dev defaults are already defined in `.env.example`.

Common commands from `apps/backend`:

```powershell
py -m alembic upgrade head
py -m alembic revision --autogenerate -m "describe change"
py -m alembic downgrade -1
```

Environment configuration:

- Local backend defaults live in `.env.example`.
- Environment-level templates live in `../../infra/environments/`.
- Backend variables use the `OPS_AGENT_` prefix.
- `OPS_AGENT_POSTGRES_DSN`, `OPS_AGENT_REDIS_URL`, `OPS_AGENT_AI_PROVIDER_API_KEY`, and key-management references should come from a secret store outside local development.
- List values such as `OPS_AGENT_CORS_ORIGINS` and `OPS_AGENT_ALLOWED_UPLOAD_MIME_TYPES` may be comma-separated in `.env` files.
