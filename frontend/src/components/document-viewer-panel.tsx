import { EmptyState } from "@/components/empty-state";
import type { DocumentSummary } from "@/lib/types";

export function DocumentViewerPanel({ documents }: { documents: DocumentSummary[] }) {
  if (documents.length === 0) {
    return (
      <EmptyState
        title="No documents available"
        detail="The case has not received any stored document metadata yet."
      />
    );
  }

  return (
    <section className="panel">
      <h2>Document Viewer</h2>
      <p className="muted">
        Source documents stay visible beside extracted evidence so reviewers can verify machine outputs before taking
        action.
      </p>
      <div className="document-grid">
        {documents.map((doc) => (
          <article className="document-card" key={doc.document_id}>
            <div className="document-preview">PDF</div>
            <div>
              <strong>{doc.filename}</strong>
              <div className="muted">{doc.document_id}</div>
              <div className="muted">
                {doc.mime_type} | {doc.page_count ?? "?"} pages
              </div>
              {doc.file_hash ? <div className="muted">Hash: {doc.file_hash}</div> : null}
              <div className="pill-row">
                <span className="pill">{doc.status}</span>
                <span className="pill">{doc.source_channel}</span>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
