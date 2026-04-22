import type { ComplianceFinding, EvidenceReference, RiskFinding, ValidationFinding } from "@/api/contracts";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { cn } from "@/lib/cn";

interface FindingsPanelProps {
  validationFindings: ValidationFinding[];
  riskFindings: RiskFinding[];
  complianceFindings: ComplianceFinding[];
}

type FindingOutcome = "pass" | "warning" | "fail";
type FindingGroup = "validation" | "risk" | "compliance";

interface FindingsPanelItem {
  id: string;
  group: FindingGroup;
  code: string;
  title: string;
  explanation: string;
  linkedField: string | null;
  severityLabel: string;
  statusLabel: string;
  outcome: FindingOutcome;
  isBlocking: boolean;
  evidenceCount: number;
}

const outcomeStyles: Record<FindingOutcome, string> = {
  pass: "border-[#cfe9d9] bg-[#f4fbf6]",
  warning: "border-warningSoft bg-[#fff9ef]",
  fail: "border-dangerSoft bg-[#fff4f4]",
};

const outcomeTones: Record<FindingOutcome, "success" | "warning" | "danger"> = {
  pass: "success",
  warning: "warning",
  fail: "danger",
};

function prettify(value: string) {
  return value.split("_").join(" ");
}

function getLinkedField(fieldName: string | null | undefined, evidenceRefs: EvidenceReference[]) {
  if (fieldName) {
    return prettify(fieldName);
  }

  const evidenceField = evidenceRefs.find((reference) => reference.metadata.field_name)?.metadata.field_name;
  return evidenceField ? prettify(evidenceField) : null;
}

function buildValidationItem(finding: ValidationFinding): FindingsPanelItem {
  const isBlocking = finding.status === "open" && (finding.severity === "error" || finding.severity === "critical");
  const outcome: FindingOutcome = finding.status !== "open" ? "pass" : isBlocking ? "fail" : "warning";

  return {
    id: finding.id,
    group: "validation",
    code: finding.rule_code,
    title: prettify(finding.rule_code),
    explanation: finding.message,
    linkedField: getLinkedField(finding.field_name, finding.evidence_refs),
    severityLabel: prettify(finding.severity),
    statusLabel: prettify(finding.status),
    outcome,
    isBlocking,
    evidenceCount: finding.evidence_refs.length,
  };
}

function buildRiskItem(finding: RiskFinding): FindingsPanelItem {
  const isBlocking = finding.status === "open" && (finding.risk_level === "high" || finding.risk_level === "critical");
  const outcome: FindingOutcome = finding.status !== "open" ? "pass" : isBlocking ? "fail" : "warning";

  return {
    id: finding.id,
    group: "risk",
    code: finding.risk_code,
    title: prettify(finding.risk_code),
    explanation: finding.message,
    linkedField: getLinkedField(null, finding.evidence_refs),
    severityLabel: prettify(finding.risk_level),
    statusLabel: prettify(finding.status),
    outcome,
    isBlocking,
    evidenceCount: finding.evidence_refs.length,
  };
}

function buildComplianceItem(finding: ComplianceFinding): FindingsPanelItem {
  const isBlocking = finding.status === "open" && (finding.severity === "error" || finding.severity === "critical");
  const outcome: FindingOutcome = finding.status !== "open" ? "pass" : isBlocking ? "fail" : "warning";

  return {
    id: finding.id,
    group: "compliance",
    code: finding.policy_code,
    title: prettify(finding.policy_code),
    explanation: finding.message,
    linkedField: getLinkedField(null, finding.evidence_refs),
    severityLabel: prettify(finding.severity),
    statusLabel: finding.regulation_reference ? `${prettify(finding.status)} | ${finding.regulation_reference}` : prettify(finding.status),
    outcome,
    isBlocking,
    evidenceCount: finding.evidence_refs.length,
  };
}

export function FindingsPanel({ validationFindings, riskFindings, complianceFindings }: FindingsPanelProps) {
  const sections = [
    {
      key: "validation" as const,
      title: "Validation findings",
      description: "Data quality and rule-level checks.",
      items: validationFindings.map(buildValidationItem),
    },
    {
      key: "risk" as const,
      title: "Risk findings",
      description: "Fraud, risk, or adverse-signal checks.",
      items: riskFindings.map(buildRiskItem),
    },
    {
      key: "compliance" as const,
      title: "Compliance findings",
      description: "Policy and regulatory checks.",
      items: complianceFindings.map(buildComplianceItem),
    },
  ];

  const allItems = sections.flatMap((section) => section.items);
  const summary = {
    fail: allItems.filter((item) => item.outcome === "fail").length,
    warning: allItems.filter((item) => item.outcome === "warning").length,
    pass: allItems.filter((item) => item.outcome === "pass").length,
  };

  return (
    <Card title="Review findings" description="Grouped review findings with clear blocking cues so reviewers can separate critical failures from monitor-only issues.">
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-dangerSoft bg-[#fff4f4] p-4">
          <p className="eyebrow">Blocking</p>
          <p className="mt-3 text-3xl font-semibold text-danger">{summary.fail}</p>
          <p className="mt-1 text-sm text-slate">Must be addressed before approval</p>
        </div>
        <div className="rounded-2xl border border-warningSoft bg-[#fff9ef] p-4">
          <p className="eyebrow">Warnings</p>
          <p className="mt-3 text-3xl font-semibold text-warning">{summary.warning}</p>
          <p className="mt-1 text-sm text-slate">Non-blocking issues that still need review</p>
        </div>
        <div className="rounded-2xl border border-[#cfe9d9] bg-[#f4fbf6] p-4">
          <p className="eyebrow">Passed or closed</p>
          <p className="mt-3 text-3xl font-semibold text-[#137547]">{summary.pass}</p>
          <p className="mt-1 text-sm text-slate">Resolved, waived, or non-open findings</p>
        </div>
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-3">
        {sections.map((section) => (
          <section key={section.key} className="rounded-2xl border border-line bg-white p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold text-ink">{section.title}</h3>
                <p className="mt-1 text-sm text-slate">{section.description}</p>
              </div>
              <StatusBadge tone="neutral">{String(section.items.length)}</StatusBadge>
            </div>

            {section.items.length === 0 ? (
              <p className="mt-4 text-sm text-slate">No findings recorded.</p>
            ) : (
              <div className="mt-4 space-y-3">
                {section.items.map((item) => (
                  <div key={item.id} className={cn("rounded-2xl border p-4", outcomeStyles[item.outcome])}>
                    <div className="flex flex-wrap items-center gap-2">
                      <h4 className="text-sm font-semibold text-ink">{item.title}</h4>
                      <StatusBadge tone={outcomeTones[item.outcome]}>{item.outcome}</StatusBadge>
                      <StatusBadge tone={item.isBlocking ? "danger" : "neutral"}>{item.severityLabel}</StatusBadge>
                      {item.isBlocking ? <StatusBadge tone="danger">blocking</StatusBadge> : null}
                    </div>

                    <p className="mt-3 text-sm leading-6 text-slate">{item.explanation}</p>

                    <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2 text-xs text-slate">
                      <span>Status: {item.statusLabel}</span>
                      <span>Code: {item.code}</span>
                      <span>Evidence refs: {item.evidenceCount}</span>
                      {item.linkedField ? <span>Linked field: {item.linkedField}</span> : null}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        ))}
      </div>
    </Card>
  );
}
