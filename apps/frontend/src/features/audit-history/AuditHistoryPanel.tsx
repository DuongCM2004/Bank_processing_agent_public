import { Panel } from "@/components/ui/Panel";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type { AuditEvent } from "@/types/api";
import { formatDateTime, humanize } from "@/utils/format";

interface AuditHistoryPanelProps {
  events: AuditEvent[];
  totalEvents: number;
}

export function AuditHistoryPanel({ events, totalEvents }: AuditHistoryPanelProps) {
  return (
    <Panel title="Audit history" description="System and human actions are separated by actor type for review traceability.">
      {events.length === 0 ? (
        <p className="text-sm text-muted">No audit events were returned for this case.</p>
      ) : (
        <ol className="relative space-y-3 border-l border-line pl-4">
          {events.map((event) => (
            <li key={event.id} className="rounded-md border border-line bg-surface p-3">
              <div className="flex flex-wrap items-center gap-2">
                <StatusBadge label={event.actor_type} tone={event.actor_type === "user" ? "info" : "neutral"} />
                <span className="text-xs font-semibold uppercase tracking-wider text-muted">{humanize(event.event_type)}</span>
              </div>
              <p className="mt-2 text-sm font-semibold text-ink">{event.summary}</p>
              <p className="mt-1 text-xs text-muted">
                {formatDateTime(event.occurred_at)} by {event.actor_identifier ?? event.actor_user_id ?? event.actor_type}
              </p>
            </li>
          ))}
        </ol>
      )}
      <p className="mt-4 text-xs text-muted">Showing {events.length} of {totalEvents} events.</p>
    </Panel>
  );
}
