from __future__ import annotations

from typing import Protocol
from uuid import UUID

from pydantic import BaseModel, Field


class TaskEnvelope(BaseModel):
    task_name: str
    entity_id: str
    correlation_id: str
    attempt_number: int = Field(default=1, ge=1)
    payload: dict[str, object] = Field(default_factory=dict)


class TaskDispatcher(Protocol):
    def enqueue(self, envelope: TaskEnvelope, *, queue_name: str) -> None:
        """Publish a task envelope to the configured worker transport."""


class InMemoryTaskDispatcher:
    def __init__(self) -> None:
        self.enqueued: list[tuple[str, TaskEnvelope]] = []

    def enqueue(self, envelope: TaskEnvelope, *, queue_name: str) -> None:
        self.enqueued.append((queue_name, envelope))


class CaseProcessingTask(BaseModel):
    case_id: UUID
    correlation_id: str
    attempt_number: int = Field(default=1, ge=1)
    requested_by: str | None = None

    def to_envelope(self) -> TaskEnvelope:
        return TaskEnvelope(
            task_name="case.process",
            entity_id=str(self.case_id),
            correlation_id=self.correlation_id,
            attempt_number=self.attempt_number,
            payload={"case_id": str(self.case_id), "requested_by": self.requested_by},
        )
