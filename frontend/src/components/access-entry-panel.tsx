import Link from "next/link";

import { getDefaultLandingRoute } from "@/lib/auth";
import type { CurrentUser } from "@/lib/types";

export function AccessEntryPanel({ user }: { user: CurrentUser }) {
  return (
    <section className="panel hero-panel">
      <p className="eyebrow">Controlled Access</p>
      <h1>Ops Agent Access Entry</h1>
      <p className="muted">
        This entry point is intentionally narrow. Reviewers land in queue-driven workflows with audit and evidence preserved.
      </p>
      <div className="pill-row">
        <span className="pill">human review preserved</span>
        <span className="pill">evidence-linked</span>
        <span className="pill">audit-ready</span>
      </div>
      <div className="cta-row">
        <Link href={getDefaultLandingRoute(user)} className="action-link primary">
          Enter workspace
        </Link>
        <Link href="/login" className="action-link">
          Change account
        </Link>
      </div>
    </section>
  );
}
