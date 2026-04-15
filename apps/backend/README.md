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
