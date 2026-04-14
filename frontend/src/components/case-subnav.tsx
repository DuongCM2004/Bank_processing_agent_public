import Link from "next/link";

export function CaseSubnav({ caseId }: { caseId: string }) {
  return (
    <section className="subnav">
      <Link href={`/cases/${caseId}`}>Overview</Link>
      <Link href={`/cases/${caseId}/documents`}>Documents</Link>
      <Link href={`/cases/${caseId}/review`}>Review</Link>
      <Link href={`/cases/${caseId}/audit`}>Audit</Link>
    </section>
  );
}
