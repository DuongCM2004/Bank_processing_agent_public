import { EmptyState } from "@/components/empty-state";
import type { EvidenceRef } from "@/lib/types";

export function EvidenceDrawer({ evidence }: { evidence: EvidenceRef[] }) {
  if (evidence.length === 0) {
    return (
      <EmptyState
        title="No linked evidence"
        detail="Evidence anchors will appear once extraction or validation steps attach document references."
      />
    );
  }

  return (
    <div className="panel">
      <h3>Evidence Links</h3>
      <div className="evidence-list">
        {evidence.map((item, index) => (
          <div className="evidence-item" key={`${item.document_id}-${index}`}>
            <div>
              <strong>Document:</strong> {item.document_id}
            </div>
            <div>
              <strong>Page:</strong> {item.page_number ?? "n/a"}
            </div>
            <div>
              <strong>Text:</strong> {item.text_span ?? "not captured"}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
