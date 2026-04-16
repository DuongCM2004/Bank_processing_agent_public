import { StatusBadge } from "@/components/ui/StatusBadge";
import type { DocumentUploadMetadata } from "@/types/api";
import { formatBytes, formatDateTime } from "@/utils/format";

interface LinkedDocumentsProps {
  documents: DocumentUploadMetadata[];
  selectedDocumentId: string | null;
  onSelectDocument: (documentId: string) => void;
}

export function LinkedDocuments({ documents, selectedDocumentId, onSelectDocument }: LinkedDocumentsProps) {
  if (documents.length === 0) {
    return <p className="text-sm text-muted">No linked documents were returned by the backend.</p>;
  }

  return (
    <div className="space-y-2">
      {documents.map((document) => (
        <button
          key={document.id}
          type="button"
          onClick={() => onSelectDocument(document.id)}
          className={`w-full rounded-md border p-3 text-left transition ${
            document.id === selectedDocumentId ? "border-teal bg-tealSoft" : "border-line bg-panel hover:bg-surface"
          }`}
        >
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="font-semibold text-ink">{document.filename}</p>
            <StatusBadge label={document.status} tone={document.status === "failed" ? "danger" : "neutral"} />
          </div>
          <p className="mt-2 text-xs text-muted">
            {document.document_type} | {formatBytes(document.file_size_bytes)} | Uploaded {formatDateTime(document.uploaded_at)}
          </p>
        </button>
      ))}
    </div>
  );
}
