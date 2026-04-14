from __future__ import annotations

from ops_agent.models import AuditEvent, CaseRecord, CaseResults, DocumentRecord, ReviewActionRecord, ReviewTaskRecord


class PostgresRepository:
    """Starter repository contract for future relational persistence.

    Keep the method surface aligned with the in-memory repository during the
    migration period. Add transaction and outbox support before production use.
    """

    def save_case(self, case: CaseRecord) -> CaseRecord:
        raise NotImplementedError

    def get_case(self, case_id: str) -> CaseRecord | None:
        raise NotImplementedError

    def save_document(self, document: DocumentRecord) -> DocumentRecord:
        raise NotImplementedError

    def get_document(self, document_id: str) -> DocumentRecord | None:
        raise NotImplementedError

    def save_review_task(self, task: ReviewTaskRecord) -> ReviewTaskRecord:
        raise NotImplementedError

    def get_review_task(self, task_id: str) -> ReviewTaskRecord | None:
        raise NotImplementedError

    def list_review_tasks(self, *, status: str | None = None) -> list[ReviewTaskRecord]:
        raise NotImplementedError

    def save_results(self, results: CaseResults) -> CaseResults:
        raise NotImplementedError

    def get_results(self, case_id: str) -> CaseResults | None:
        raise NotImplementedError

    def save_review_action(self, action: ReviewActionRecord) -> ReviewActionRecord:
        raise NotImplementedError

    def save_audit_event(self, event: AuditEvent) -> AuditEvent:
        raise NotImplementedError

    def list_audit_events(self, case_id: str) -> list[AuditEvent]:
        raise NotImplementedError
