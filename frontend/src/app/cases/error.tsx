"use client";

import { ErrorState } from "@/components/error-state";

export default function CasesError({ error }: { error: Error & { digest?: string } }) {
  return (
    <main className="shell">
      <ErrorState title="Unable to load case list" detail={error.message} />
    </main>
  );
}
