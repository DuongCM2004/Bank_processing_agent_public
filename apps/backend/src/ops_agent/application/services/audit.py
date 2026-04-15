from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from fastapi.encoders import jsonable_encoder

from ops_agent.api.schemas import AuditEventListResponse, AuditEventResponse, EvidenceReferenceResponse
from ops_agent.domain.shared.enums import AuditActorType, AuditEventType, DecisionType, ManualReviewActionType
from ops_agent.domain.shared.exceptions import ResourceNotFoundError
from ops_agent.domain.workflow import CaseTransitionAuditRecord
from ops_agent.infrastructure.db.models import AuditEvent
from ops_agent.infrastructure.db.repositories import AuditEventFilters, AuditRepository


@dataclass(frozen=True, slots=True)
class AuditActor:
    actor_type: AuditActorType
    actor_identifier: str | None = None
    actor_user_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class AuditTarget:
    resource_type: str
    resource_id: UUID
    case_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class AuditEventCommand:
    event_type: AuditEventType
    summary: str
    target: AuditTarget
    actor: AuditActor
    metadata_payload: dict[str, object] = field(default_factory=dict)
    evidence_refs: list[object] = field(default_factory=list)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_by: str | None = None
    updated_by: str | None = None


class AuditService:
    def __init__(self, repository: AuditRepository) -> None:
        self._repository = repository

    def record_event(self, command: AuditEventCommand) -> AuditEvent:
        event = AuditEvent(
            case_id=command.target.case_id,
            actor_user_id=command.actor.actor_user_id,
            actor_type=command.actor.actor_type,
            actor_identifier=command.actor.actor_identifier,
            event_type=command.event_type,
            summary=command.summary,
            resource_type=command.target.resource_type,
            resource_id=command.target.resource_id,
            occurred_at=command.occurred_at,
            details=self._normalize_payload(command.metadata_payload),
            evidence_refs=self._normalize_payload(command.evidence_refs),
            created_by=command.created_by or command.actor.actor_identifier,
            updated_by=command.updated_by or command.actor.actor_identifier,
        )
        self._repository.add_event(event)
        return event

    def record_case_transition(self, event: CaseTransitionAuditRecord) -> AuditEvent:
        return self.record_event(
            AuditEventCommand(
                event_type=event.event_type,
                summary=f"Case status changed from '{event.from_status.value}' to '{event.to_status.value}'.",
                target=AuditTarget(resource_type="case", resource_id=event.case_id, case_id=event.case_id),
                actor=AuditActor(
                    actor_type=event.actor_type,
                    actor_identifier=event.actor_id,
                    actor_user_id=_maybe_uuid(event.actor_id) if event.actor_type == AuditActorType.USER else None,
                ),
                metadata_payload={
                    "from_status": event.from_status.value,
                    "to_status": event.to_status.value,
                    "transition_name": event.transition_name,
                    "reason_code": event.reason_code,
                    "comment": event.comment,
                    "metadata": event.metadata,
                },
                occurred_at=event.occurred_at,
                created_by=event.actor_id,
                updated_by=event.actor_id,
            )
        )

    def record_document_uploaded(
        self,
        *,
        case_id: UUID,
        document_id: UUID,
        actor_user_id: UUID | None,
        actor_identifier: str,
        actor_type: AuditActorType,
        filename: str,
        mime_type: str,
        file_size_bytes: int,
        storage_key: str,
        occurred_at: datetime,
    ) -> AuditEvent:
        return self.record_event(
            AuditEventCommand(
                event_type=AuditEventType.DOCUMENT_ADDED,
                summary=f"Document '{filename}' was uploaded to the case.",
                target=AuditTarget(resource_type="document", resource_id=document_id, case_id=case_id),
                actor=AuditActor(
                    actor_type=actor_type,
                    actor_identifier=actor_identifier,
                    actor_user_id=actor_user_id,
                ),
                metadata_payload={
                    "filename": filename,
                    "mime_type": mime_type,
                    "file_size_bytes": file_size_bytes,
                    "storage_key": storage_key,
                },
                occurred_at=occurred_at,
                created_by=actor_identifier,
                updated_by=actor_identifier,
            )
        )

    def record_manual_review_action(
        self,
        *,
        case_id: UUID,
        action_id: UUID,
        performed_by_user_id: UUID,
        action_type: ManualReviewActionType,
        document_id: UUID | None,
        comment: str | None,
        payload: dict[str, object],
        evidence_refs: list[object],
        occurred_at: datetime,
    ) -> AuditEvent:
        return self.record_event(
            AuditEventCommand(
                event_type=AuditEventType.MANUAL_REVIEW_ACTION_RECORDED,
                summary=f"Manual review action '{action_type.value}' was recorded.",
                target=AuditTarget(resource_type="manual_review_action", resource_id=action_id, case_id=case_id),
                actor=AuditActor(
                    actor_type=AuditActorType.USER,
                    actor_identifier=str(performed_by_user_id),
                    actor_user_id=performed_by_user_id,
                ),
                metadata_payload={
                    "action_type": action_type.value,
                    "document_id": str(document_id) if document_id else None,
                    "comment": comment,
                    "payload": payload,
                },
                evidence_refs=evidence_refs,
                occurred_at=occurred_at,
                created_by=str(performed_by_user_id),
                updated_by=str(performed_by_user_id),
            )
        )

    def record_decision(
        self,
        *,
        case_id: UUID,
        decision_id: UUID,
        decided_by_user_id: UUID,
        decision_type: DecisionType,
        outcome: str,
        reason_code: str,
        linked_findings: list[dict[str, object]],
        evidence_refs: list[object],
        occurred_at: datetime,
    ) -> AuditEvent:
        return self.record_event(
            AuditEventCommand(
                event_type=AuditEventType.DECISION_RECORDED,
                summary=f"Decision '{outcome}' was recorded for the case.",
                target=AuditTarget(resource_type="decision", resource_id=decision_id, case_id=case_id),
                actor=AuditActor(
                    actor_type=AuditActorType.USER,
                    actor_identifier=str(decided_by_user_id),
                    actor_user_id=decided_by_user_id,
                ),
                metadata_payload={
                    "outcome": outcome,
                    "reason_code": reason_code,
                    "decision_type": decision_type.value,
                    "linked_findings": linked_findings,
                },
                evidence_refs=evidence_refs,
                occurred_at=occurred_at,
                created_by=str(decided_by_user_id),
                updated_by=str(decided_by_user_id),
            )
        )

    def list_case_events(
        self,
        *,
        case_id: UUID,
        limit: int,
        offset: int,
        event_type: AuditEventType | None = None,
        actor_type: AuditActorType | None = None,
        resource_type: str | None = None,
    ) -> AuditEventListResponse:
        if not self._repository.case_exists(case_id):
            raise ResourceNotFoundError("Case", str(case_id))
        items, total = self._repository.list_case_events(
            case_id=case_id,
            filters=AuditEventFilters(event_type=event_type, actor_type=actor_type, resource_type=resource_type),
            limit=limit,
            offset=offset,
        )
        return AuditEventListResponse(
            items=[self.to_response(item) for item in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    @staticmethod
    def to_response(item: AuditEvent) -> AuditEventResponse:
        return AuditEventResponse(
            id=item.id,
            case_id=item.case_id,
            actor_user_id=item.actor_user_id,
            actor_type=item.actor_type,
            actor_identifier=item.actor_identifier,
            event_type=item.event_type,
            summary=item.summary,
            resource_type=item.resource_type,
            resource_id=item.resource_id,
            occurred_at=item.occurred_at,
            metadata=item.details,
            evidence_refs=[EvidenceReferenceResponse.model_validate(ref) for ref in item.evidence_refs],
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @staticmethod
    def _normalize_payload(value: object) -> object:
        return jsonable_encoder(value)


def _maybe_uuid(value: str | None) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(value)
    except ValueError:
        return None
