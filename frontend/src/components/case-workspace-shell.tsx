import type { ReactNode } from "react";

import { CaseHeader } from "@/components/case-header";
import { CaseSubnav } from "@/components/case-subnav";
import type { CaseWorkspaceData } from "@/lib/types";

export function CaseWorkspaceShell({
  workspace,
  children,
}: {
  workspace: CaseWorkspaceData;
  children: ReactNode;
}) {
  return (
    <section className="shell">
      <CaseHeader workspace={workspace} />
      <CaseSubnav caseId={workspace.caseRecord.case_id} />
      {children}
    </section>
  );
}
