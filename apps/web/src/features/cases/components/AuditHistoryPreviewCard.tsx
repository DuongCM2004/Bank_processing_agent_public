import type { AuditEvent } from "@/api/contracts";
import { Card } from "@/components/ui/Card";

interface AuditHistoryPreviewCardProps {
  events: AuditEvent[];
  totalEvents: number;
}

export function AuditHistoryPreviewCard({ events, totalEvents }: AuditHistoryPreviewCardProps) {
  return (
    <Card
      title="Audit history preview"
      description="Recent structured audit activity. Full timeline can be expanded later without changing the section contract."
    >
      <div className="space-y-3">
        <p className="text-sm text-slate">{totalEvents} total audit events recorded</p>
        {events.length === 0 ? (
          <p className="text-sm text-slate">No audit activity available.</p>
        ) : (
          events.map((event) => (
            <div key={event.id} className="rounded-2xl border border-line p-4">
              <p className="text-sm font-semibold text-ink">{event.summary}</p>
              <p className="mt-1 text-xs uppercase tracking-wide text-slate">
                {event.event_type} · {event.resource_type}
              </p>
              <p className="mt-2 text-xs text-slate">{new Date(event.occurred_at).toLocaleString()}</p>
            </div>
          ))
        )}
      </div>
    </Card>
  );
}
