# Local Docker Development

This setup is intentionally local-development only. It runs the API, web dashboard, PostgreSQL, and Redis on one Docker bridge network.

## Start

From the repository root:

```powershell
docker compose up --build
```

Open:

- Web dashboard: `http://localhost:5173`
- Backend OpenAPI: `http://localhost:8003/docs`
- Backend health: `http://localhost:8003/api/v1/health`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

## Volumes

- `postgres_data`: local PostgreSQL data.
- `redis_data`: local Redis append-only data.
- `backend_uploads`: uploaded document files for local development.
- `web_node_modules`: frontend dependencies installed inside the container.

To reset local state:

```powershell
docker compose down -v
```

## Networking

Containers share the `ops_agent_local` bridge network. The backend uses service DNS names:

- PostgreSQL: `postgres:5432`
- Redis: `redis:6379`

The browser still calls the API through the host-mapped URL `http://localhost:8003/api/v1`.

## Startup Notes

- The backend waits for Postgres and Redis health checks before starting.
- The backend runs `alembic upgrade head` before starting Uvicorn.
- Source folders are bind-mounted for local reload behavior.
- This is not a production orchestration model; production should use managed secrets, external persistence, hardened images, and platform-specific health/routing controls.
