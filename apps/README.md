# Apps

Executable runtimes live here.

- `backend/`: FastAPI REST API, domain services, persistence, and HTTP-facing tests.
- `worker/`: background job runtime for OCR, parsing, classification, extraction, validation, and retry-safe workflow tasks.
- `web/`: React + TypeScript + Vite operations dashboard for case review and evidence handling.

Keep app-local tests with each app. Reserve root `tests/e2e` for cross-app system flows only.
