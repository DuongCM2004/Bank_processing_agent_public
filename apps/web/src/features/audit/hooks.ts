import { useQuery } from "@tanstack/react-query";

import type { AuditActorType, AuditEventType } from "@/api/contracts";
import { listAuditEventsByUuid, listCaseAuditEvents } from "@/features/audit/api";

export function useCaseAuditEventsQuery(filters: {
  caseId?: string;
  eventType?: AuditEventType;
  actorType?: AuditActorType;
  resourceType?: string;
}) {
  return useQuery({
    queryKey: ["case-audit-events", filters],
    queryFn: () =>
      listCaseAuditEvents({
        caseId: filters.caseId!,
        eventType: filters.eventType,
        actorType: filters.actorType,
        resourceType: filters.resourceType,
      }),
    enabled: Boolean(filters.caseId),
  });
}

export function useUuidAuditEventsQuery(filters: {
  entityUuid?: string;
  eventType?: AuditEventType;
  actorType?: AuditActorType;
  resourceType?: string;
}) {
  return useQuery({
    queryKey: ["uuid-audit-events", filters.entityUuid, filters],
    queryFn: () =>
      listAuditEventsByUuid(filters.entityUuid!, {
        eventType: filters.eventType,
        actorType: filters.actorType,
        resourceType: filters.resourceType,
      }),
    enabled: Boolean(filters.entityUuid),
  });
}
