import type { AuditEvent } from "@/api/contracts";
import { Card } from "@/components/ui/Card";

export function AuditEventList({ events }: { events: AuditEvent[] }) {
  return (
    <Card title="Audit events" description="Structured compliance-grade activity trail for this case.">
      <div className="space-y-4">
        {events.map((event) => (
          <article key={event.id} className="rounded-2xl border border-line p-4">
            <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
              <div>
                <p className="text-sm font-semibold text-ink">{event.summary}</p>
                <p className="mt-1 text-xs uppercase tracking-wide text-slate">
                  {event.event_type} · {event.resource_type}
                </p>
              </div>
              <p className="text-xs text-slate">{new Date(event.occurred_at).toLocaleString()}</p>
            </div>
            {Object.keys(event.metadata).length > 0 ? (
              <pre className="mt-3 overflow-x-auto rounded-xl bg-mist p-3 text-xs text-slate">
                {JSON.stringify(event.metadata, null, 2)}
              </pre>
            ) : null}
          </article>
        ))}
      </div>
    </Card>
  );
}
