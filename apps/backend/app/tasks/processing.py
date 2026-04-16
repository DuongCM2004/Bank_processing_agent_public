from __future__ import annotations

from uuid import UUID

from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.processing.process_case_documents")
def process_case_documents(case_id: str) -> dict[str, str]:
    parsed_case_id = UUID(case_id)
    return {
        "case_id": str(parsed_case_id),
        "status": "queued",
        "detail": "Provider execution is intentionally deferred behind provider interfaces.",
    }

