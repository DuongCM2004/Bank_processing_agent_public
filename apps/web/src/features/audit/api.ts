import { apiClient } from "@/api/client";
import type { AuditActorType, AuditEventListResponse, AuditEventType } from "@/api/contracts";

interface ListCaseAuditEventsParams {
  caseId: string;
  limit?: number;
  offset?: number;
  eventType?: AuditEventType;
  actorType?: AuditActorType;
  resourceType?: string;
}

export function listCaseAuditEvents(params: ListCaseAuditEventsParams) {
  return apiClient.get<AuditEventListResponse>(`/cases/${params.caseId}/audit-events`, {
    limit: params.limit ?? 50,
    offset: params.offset ?? 0,
    event_type: params.eventType,
    actor_type: params.actorType,
    resource_type: params.resourceType,
  });
}
