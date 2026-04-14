import { EmptyState } from "@/components/empty-state";
import type { AuditEvent } from "@/lib/types";

export function AuditHistoryPanel({ items }: { items: AuditEvent[] }) {
  if (items.length === 0) {
    return (
      <EmptyState
        title="No audit events recorded"
        detail="Audit history will appear once the case is created, processed, or reviewed."
      />
    );
  }

  return (
    <section className="panel">
      <h2>Audit History</h2>
      <p className="muted">
        Append-only event timeline for compliance review, investigation, and evidence-backed change tracking.
      </p>
      <div className="audit-list">
        {items.map((item) => (
          <article key={item.event_id} className="audit-item">
            <div className="audit-head">
              <strong>{item.action}</strong>
              <span className="muted">{item.occurred_at}</span>
            </div>
            <div className="muted">
              {item.actor_type} | {item.actor_id} | {item.resource_type}/{item.resource_id}
            </div>
            <pre className="json-preview">{JSON.stringify(item.details, null, 2)}</pre>
          </article>
        ))}
      </div>
    </section>
  );
}
