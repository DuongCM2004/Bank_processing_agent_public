import { Card } from "@/components/ui/Card";
import { PageHeader } from "@/components/ui/PageHeader";

export function SettingsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Configuration"
        title="Frontend settings"
        description="Operational UI configuration and environment visibility for local development and future admin tooling."
      />

      <Card title="API configuration" description="Transport-layer settings currently wired into the frontend scaffold.">
        <dl className="grid gap-4 md:grid-cols-2">
          <div className="rounded-2xl border border-line p-4">
            <dt className="eyebrow">API base URL</dt>
            <dd className="mt-2 text-sm font-medium text-ink">{import.meta.env.VITE_API_BASE_URL ?? "/api/v1"}</dd>
          </div>
          <div className="rounded-2xl border border-line p-4">
            <dt className="eyebrow">Testing</dt>
            <dd className="mt-2 text-sm font-medium text-ink">Vitest + React Testing Library</dd>
          </div>
        </dl>
      </Card>
    </div>
  );
}
