# Environment Configuration

Environment variables are split by audience and sensitivity:

- Backend variables use the `OPS_AGENT_` prefix and are read by `ops_agent.config.AppSettings`.
- Frontend variables use the `VITE_OPS_AGENT_` prefix and are public because Vite embeds them in the browser bundle.
- Committed `*.env.example` files contain safe defaults or placeholders only.
- Filled secret files must not be committed; use a platform secret store for shared environments.

## Files

- `local.env.example`: local non-sensitive defaults for backend, queue, storage, AI placeholder mode, and frontend.
- `staging.env.example`: non-sensitive staging template.
- `production.env.example`: non-sensitive production template.
- `secrets.env.example`: placeholders for secret values that must be supplied separately.

## Sensitive Variables

- `OPS_AGENT_POSTGRES_DSN`
- `OPS_AGENT_REDIS_URL`
- `OPS_AGENT_AI_PROVIDER_API_KEY`
- `OPS_AGENT_STORAGE_KMS_KEY_ID`

Local examples may include disposable credentials for developer containers. Staging and production must source these values from secret management, not committed files.

## Non-Sensitive Runtime Variables

- `OPS_AGENT_ENV`
- `OPS_AGENT_APP_NAME`
- `OPS_AGENT_DEBUG`
- `OPS_AGENT_API_V1_PREFIX`
- `OPS_AGENT_CORS_ORIGINS`
- `OPS_AGENT_LOG_LEVEL`
- `OPS_AGENT_LOG_JSON`
- `OPS_AGENT_TASK_QUEUE_NAME`
- `OPS_AGENT_AI_PROVIDER_MODE`
- `OPS_AGENT_AI_PROVIDER_ENDPOINT`
- `OPS_AGENT_AI_PROVIDER_TIMEOUT_SECONDS`
- `OPS_AGENT_PROCESSING_MAX_RETRY_ATTEMPTS`
- `OPS_AGENT_PROCESSING_MIN_OCR_CONFIDENCE`
- `OPS_AGENT_PROCESSING_MIN_EXTRACTION_CONFIDENCE`
- `OPS_AGENT_STORAGE_BACKEND`
- `OPS_AGENT_STORAGE_ROOT_PATH`
- `OPS_AGENT_STORAGE_BLOB_ENDPOINT`
- `OPS_AGENT_STORAGE_BLOB_BUCKET`
- `OPS_AGENT_MAX_UPLOAD_BYTES`
- `OPS_AGENT_ALLOWED_UPLOAD_MIME_TYPES`
- `VITE_OPS_AGENT_APP_NAME`
- `VITE_OPS_AGENT_ENV`
- `VITE_OPS_AGENT_API_BASE_URL`
- `VITE_OPS_AGENT_ENABLE_MOCK_API`

## Evolution Guidance

- `local`: local Postgres and Redis, local filesystem storage, placeholder AI providers.
- `development`: shared integration environment with real persistence and sandboxed or placeholder AI providers.
- `staging`: production-like topology with JSON logs, blob storage, migration rehearsal, and locked CORS origins.
- `production`: externally managed secrets, explicit provider configuration, strict CORS, JSON logs, and environment-specific buckets or containers.

Do not add secrets to `VITE_OPS_AGENT_*`; those values are visible to every browser user.
