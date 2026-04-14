from __future__ import annotations

from collections import defaultdict
from threading import RLock

from ops_agent.models import (
    AuditEvent,
    CaseRecord,
    CaseResults,
    DecisionRecord,
    DocumentRecord,
    DocumentVersionRecord,
    ExtractionRunRecord,
    ReviewActionRecord,
    ReviewTaskRecord,
    ValidationRunRecord,
    WorkflowRunRecord,
    WorkflowRunStatus,
    WorkflowStepRunRecord,
)


class InMemoryRepository:
    def __init__(self) -> None:
        self._lock = RLock()
        self.cases: dict[str, CaseRecord] = {}
        self.documents: dict[str, DocumentRecord] = {}
        self.document_versions: dict[str, list[DocumentVersionRecord]] = defaultdict(list)
        self.review_tasks: dict[str, ReviewTaskRecord] = {}
        self.results: dict[str, CaseResults] = {}
        self.review_actions: dict[str, ReviewActionRecord] = {}
        self.audit_events: dict[str, list[AuditEvent]] = defaultdict(list)
        self.workflow_runs: dict[str, list[WorkflowRunRecord]] = defaultdict(list)
        self.workflow_step_runs: dict[str, list[WorkflowStepRunRecord]] = defaultdict(list)
        self.extraction_runs: dict[str, list[ExtractionRunRecord]] = defaultdict(list)
        self.validation_runs: dict[str, list[ValidationRunRecord]] = defaultdict(list)
        self.decisions: dict[str, list[DecisionRecord]] = defaultdict(list)

    def save_case(self, case: CaseRecord) -> CaseRecord:
        with self._lock:
            self.cases[case.case_id] = case
        return case

    def get_case(self, case_id: str) -> CaseRecord | None:
        return self.cases.get(case_id)

    def save_document(self, document: DocumentRecord) -> DocumentRecord:
        with self._lock:
            self.documents[document.document_id] = document
        return document

    def get_document(self, document_id: str) -> DocumentRecord | None:
        return self.documents.get(document_id)

    def save_document_version(self, document_version: DocumentVersionRecord) -> DocumentVersionRecord:
        with self._lock:
            versions = [item for item in self.document_versions[document_version.document_id] if item.document_version_id != document_version.document_version_id]
            versions.append(document_version)
            self.document_versions[document_version.document_id] = sorted(versions, key=lambda item: item.version_number)
        return document_version

    def list_document_versions(self, document_id: str) -> list[DocumentVersionRecord]:
        return list(self.document_versions.get(document_id, []))

    def save_review_task(self, task: ReviewTaskRecord) -> ReviewTaskRecord:
        with self._lock:
            self.review_tasks[task.task_id] = task
        return task

    def get_review_task(self, task_id: str) -> ReviewTaskRecord | None:
        return self.review_tasks.get(task_id)

    def list_review_tasks(self, *, status: str | None = None) -> list[ReviewTaskRecord]:
        items = list(self.review_tasks.values())
        if status:
            items = [item for item in items if item.status == status]
        return sorted(items, key=lambda item: item.created_at)

    def save_results(self, results: CaseResults) -> CaseResults:
        with self._lock:
            self.results[results.case_id] = results
        return results

    def get_results(self, case_id: str) -> CaseResults | None:
        return self.results.get(case_id)

    def save_review_action(self, action: ReviewActionRecord) -> ReviewActionRecord:
        with self._lock:
            self.review_actions[action.action_id] = action
        return action

    def save_audit_event(self, event: AuditEvent) -> AuditEvent:
        with self._lock:
            self.audit_events[event.case_id].append(event)
        return event

    def list_audit_events(self, case_id: str) -> list[AuditEvent]:
        return sorted(self.audit_events.get(case_id, []), key=lambda item: item.occurred_at)

    def save_workflow_run(self, workflow_run: WorkflowRunRecord) -> WorkflowRunRecord:
        with self._lock:
            runs = [item for item in self.workflow_runs[workflow_run.case_id] if item.workflow_run_id != workflow_run.workflow_run_id]
            runs.append(workflow_run)
            self.workflow_runs[workflow_run.case_id] = sorted(runs, key=lambda item: item.started_at)
        return workflow_run

    def list_workflow_runs(self, case_id: str) -> list[WorkflowRunRecord]:
        return list(self.workflow_runs.get(case_id, []))

    def get_active_workflow_run(self, case_id: str) -> WorkflowRunRecord | None:
        active_statuses = {WorkflowRunStatus.QUEUED, WorkflowRunStatus.IN_PROGRESS, WorkflowRunStatus.WAITING_REVIEW}
        runs = [item for item in self.workflow_runs.get(case_id, []) if item.status in active_statuses]
        if not runs:
            return None
        return sorted(runs, key=lambda item: item.started_at)[-1]

    def get_latest_workflow_run(self, case_id: str) -> WorkflowRunRecord | None:
        runs = self.workflow_runs.get(case_id, [])
        if not runs:
            return None
        return sorted(runs, key=lambda item: item.started_at)[-1]

    def save_workflow_step_run(self, step_run: WorkflowStepRunRecord) -> WorkflowStepRunRecord:
        with self._lock:
            steps = [item for item in self.workflow_step_runs[step_run.workflow_run_id] if item.step_run_id != step_run.step_run_id]
            steps.append(step_run)
            self.workflow_step_runs[step_run.workflow_run_id] = sorted(steps, key=lambda item: item.started_at)
        return step_run

    def list_workflow_step_runs(self, workflow_run_id: str) -> list[WorkflowStepRunRecord]:
        return list(self.workflow_step_runs.get(workflow_run_id, []))

    def save_extraction_run(self, extraction_run: ExtractionRunRecord) -> ExtractionRunRecord:
        with self._lock:
            self.extraction_runs[extraction_run.case_id].append(extraction_run)
        return extraction_run

    def list_extraction_runs(self, case_id: str) -> list[ExtractionRunRecord]:
        return list(self.extraction_runs.get(case_id, []))

    def save_validation_run(self, validation_run: ValidationRunRecord) -> ValidationRunRecord:
        with self._lock:
            self.validation_runs[validation_run.case_id].append(validation_run)
        return validation_run

    def list_validation_runs(self, case_id: str) -> list[ValidationRunRecord]:
        return list(self.validation_runs.get(case_id, []))

    def save_decision(self, decision: DecisionRecord) -> DecisionRecord:
        with self._lock:
            self.decisions[decision.case_id].append(decision)
        return decision

    def list_decisions(self, case_id: str) -> list[DecisionRecord]:
        return list(self.decisions.get(case_id, []))

    def get_latest_decision(self, case_id: str) -> DecisionRecord | None:
        decisions = self.decisions.get(case_id, [])
        if not decisions:
            return None
        return sorted(decisions, key=lambda item: item.created_at)[-1]
