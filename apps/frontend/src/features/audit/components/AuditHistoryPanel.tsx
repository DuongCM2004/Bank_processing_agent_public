import type { ReactNode } from "react";

import type { AuditEvent } from "@/api/contracts";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";

interface AuditHistoryPanelProps {
  events: AuditEvent[];
  title?: ReactNode;
  description?: ReactNode;
  totalEvents?: number;
  filterSlot?: ReactNode;
  emptyMessage?: string;
  className?: string;
}

function actorTone(actorType: AuditEvent["actor_type"]) {
  if (actorType === "user") {
    return "warning" as const;
  }

  if (actorType === "service") {
    return "active" as const;
  }

  return "neutral" as const;
}

function eventTone(eventType: AuditEvent["event_type"]) {
  if (eventType === "status_changed" || eventType === "decision_recorded") {
    return "active" as const;
  }

  if (eventType === "manual_review_action_recorded") {
    return "warning" as const;
  }

  return "neutral" as const;
}

function formatActor(event: AuditEvent) {
  return event.actor_identifier ?? event.actor_user_id ?? event.actor_type;
}

function sortChronologically(events: AuditEvent[]) {
  return [...events].sort((left, right) => Date.parse(right.occurred_at) - Date.parse(left.occurred_at));
}

export function AuditHistoryPanel({
  events,
  title = "Audit history",
  description = "Chronological structured event history for operational review and later compliance analysis.",
  totalEvents,
  filterSlot,
  emptyMessage = "No audit activity available.",
  className,
}: AuditHistoryPanelProps) {
  const orderedEvents = sortChronologically(events);

  return (
    <Card title={title} description={description} action={filterSlot} className={className}>
      <div className="space-y-4">
        {typeof totalEvents === "number" ? (
          <div className="flex flex-wrap items-center gap-2 text-sm text-slate">
            <span>{totalEvents} total audit events recorded</span>
            {filterSlot ? <span className="rounded-full bg-mist px-2.5 py-1 text-xs font-medium text-slate">filter-ready</span> : null}
          </div>
        ) : null}

        {orderedEvents.length === 0 ? (
          <p className="text-sm text-slate">{emptyMessage}</p>
        ) : (
          <div className="space-y-4">
            {orderedEvents.map((event) => (
              <article key={event.id} className="relative rounded-2xl border border-line bg-white p-4 pl-6">
                <span className="absolute left-3 top-5 h-2.5 w-2.5 rounded-full bg-accent" aria-hidden="true" />
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div className="min-w-0 space-y-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusBadge tone={eventTone(event.event_type)}>{event.event_type}</StatusBadge>
                      <StatusBadge tone={actorTone(event.actor_type)}>{event.actor_type === "user" ? "human" : event.actor_type}</StatusBadge>
                      <span className="text-xs uppercase tracking-wide text-slate">{event.resource_type}</span>
                    </div>

                    <div>
                      <p className="text-sm font-semibold text-ink">{event.summary}</p>
                      <p className="mt-1 text-sm text-slate">
                        Actor: <span className="font-medium text-ink">{formatActor(event)}</span>
                      </p>
                    </div>
                  </div>

                  <p className="shrink-0 text-xs text-slate">{new Date(event.occurred_at).toLocaleString()}</p>
                </div>

                {Object.keys(event.metadata).length > 0 ? (
                  <details className="mt-3 rounded-xl border border-dashed border-line bg-mist/70 px-3 py-3">
                    <summary className="cursor-pointer list-none text-sm font-medium text-ink">
                      Metadata preview
                    </summary>
                    <pre className="mt-3 overflow-x-auto whitespace-pre-wrap break-words text-xs leading-6 text-slate">
                      {JSON.stringify(event.metadata, null, 2)}
                    </pre>
                  </details>
                ) : null}
              </article>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
}
