import type { DocumentUploadMetadata } from "@/api/contracts";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { documentStatusTones } from "@/features/documents/status";

export function DocumentListCard({ documents }: { documents: DocumentUploadMetadata[] }) {
  return (
    <Card title="Documents" description="Stored document records linked to this case.">
      <div className="space-y-4">
        {documents.map((document) => (
          <div key={document.id} className="rounded-2xl border border-line p-4">
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div>
                <p className="font-semibold text-ink">{document.filename}</p>
                <p className="mt-1 text-sm text-slate">
                  {document.document_type} · {document.mime_type} · {(document.file_size_bytes ?? 0).toLocaleString()} bytes
                </p>
                <p className="mt-2 text-xs text-slate">Uploaded {new Date(document.uploaded_at).toLocaleString()}</p>
              </div>
              <StatusBadge tone={documentStatusTones[document.status]}>{document.status}</StatusBadge>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
