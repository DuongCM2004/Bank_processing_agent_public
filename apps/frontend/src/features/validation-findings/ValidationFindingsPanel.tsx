import { Panel } from "@/components/ui/Panel";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type { ComplianceFinding, RiskFinding, ValidationFinding } from "@/types/api";
import { humanize } from "@/utils/format";
import { severityTone } from "@/utils/status";

interface ValidationFindingsPanelProps {
  validationFindings: ValidationFinding[];
  riskFindings: RiskFinding[];
  complianceFindings: ComplianceFinding[];
  hasBlockingFindings: boolean;
}

export function ValidationFindingsPanel({
  validationFindings,
  riskFindings,
  complianceFindings,
  hasBlockingFindings,
}: ValidationFindingsPanelProps) {
  const allFindings = [
    ...validationFindings.map((finding) => ({
      id: finding.id,
      type: "Validation",
      code: finding.rule_code,
      message: finding.message,
      field: finding.field_name,
      severity: finding.severity,
      status: finding.status,
    })),
    ...riskFindings.map((finding) => ({
      id: finding.id,
      type: "Risk",
      code: finding.risk_code,
      message: finding.message,
      field: null,
      severity: finding.risk_level,
      status: finding.status,
    })),
    ...complianceFindings.map((finding) => ({
      id: finding.id,
      type: "Compliance",
      code: finding.policy_code,
      message: finding.message,
      field: finding.regulation_reference,
      severity: finding.severity,
      status: finding.status,
    })),
  ];

  const grouped = {
    fail: allFindings.filter((finding) => finding.severity === "critical" || finding.severity === "error" || finding.severity === "high"),
    warning: allFindings.filter((finding) => finding.severity === "warning" || finding.severity === "medium"),
    pass: allFindings.filter((finding) => finding.severity === "info" || finding.severity === "low"),
  };

  return (
    <Panel
      title="Validation findings"
      description="Blocking issues and warnings grouped for fast operational review."
      action={<StatusBadge label={hasBlockingFindings ? "Blocking" : "No blocking findings"} tone={hasBlockingFindings ? "danger" : "success"} />}
    >
      {allFindings.length === 0 ? (
        <p className="text-sm text-muted">No validation, risk, or compliance findings were returned.</p>
      ) : (
        <div className="space-y-5">
          {(["fail", "warning", "pass"] as const).map((group) => (
            <section key={group}>
              <h3 className="text-sm font-semibold text-ink">
                {humanize(group)} <span className="text-muted">({grouped[group].length})</span>
              </h3>
              <div className="mt-2 space-y-2">
                {grouped[group].length === 0 ? (
                  <p className="rounded-md border border-line bg-surface p-3 text-sm text-muted">No {group} findings.</p>
                ) : (
                  grouped[group].map((finding) => (
                    <article key={finding.id} className="rounded-md border border-line bg-panel p-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <StatusBadge label={finding.severity} tone={severityTone(finding.severity)} />
                        <span className="text-xs font-semibold uppercase tracking-wider text-muted">{finding.type}</span>
                        <span className="font-mono text-xs text-muted">{finding.code}</span>
                      </div>
                      <p className="mt-2 text-sm font-semibold text-ink">{finding.message}</p>
                      <p className="mt-1 text-xs text-muted">
                        {finding.field ? `${finding.field} | ` : ""}
                        Status: {finding.status}
                      </p>
                    </article>
                  ))
                )}
              </div>
            </section>
          ))}
        </div>
      )}
    </Panel>
  );
}
