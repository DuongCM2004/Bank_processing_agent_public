import { apiClient } from "@/api/client";
import type { AuditActorType, AuditEvent, AuditEventListResponse, AuditEventType } from "@/api/contracts";

interface ListCaseAuditEventsParams {
  caseId: string;
  limit?: number;
  offset?: number;
  eventType?: AuditEventType;
  actorType?: AuditActorType;
  resourceType?: string;
}

interface BackendAuditEvent {
  id: string;
  case_id?: string | null;
  event_type: AuditEventType;
  actor_type: AuditActorType;
  actor_id?: string | null;
  entity_type: string;
  entity_id?: string | null;
  occurred_at: string;
  message: string;
  details: Record<string, unknown>;
}

interface BackendAuditEventListResponse {
  items: BackendAuditEvent[];
  total: number;
}

function normalizeAuditEvent(event: BackendAuditEvent): AuditEvent {
  return {
    id: event.id,
    case_id: event.case_id,
    actor_id: event.actor_id,
    actor_user_id: event.actor_id,
    actor_type: event.actor_type,
    actor_identifier: event.actor_id,
    event_type: event.event_type,
    summary: event.message,
    message: event.message,
    resource_type: event.entity_type,
    entity_type: event.entity_type,
    resource_id: event.entity_id ?? "",
    entity_id: event.entity_id,
    occurred_at: event.occurred_at,
    metadata: event.details,
    details: event.details,
    evidence_refs: [],
    created_at: event.occurred_at,
    updated_at: event.occurred_at,
  };
}

export function listCaseAuditEvents(params: ListCaseAuditEventsParams) {
  const limit = params.limit ?? 50;
  const offset = params.offset ?? 0;

  return apiClient
    .get<BackendAuditEventListResponse>(`/cases/${params.caseId}/audit-events`, {
      limit,
      offset,
      event_type: params.eventType,
      actor_type: params.actorType,
      resource_type: params.resourceType,
    })
    .then(
      (response): AuditEventListResponse => ({
        items: response.items.map(normalizeAuditEvent),
        total: response.total,
        limit,
        offset,
      }),
    );
}
