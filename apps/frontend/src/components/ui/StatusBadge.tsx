import { cn } from "@/lib/cn";

interface StatusBadgeProps {
  tone: StatusBadgeTone;
  children: string;
}

export type StatusBadgeTone = "neutral" | "active" | "warning" | "danger" | "success";

const toneClasses: Record<StatusBadgeTone, string> = {
  neutral: "bg-mist text-ink",
  active: "bg-accentSoft text-accent",
  warning: "bg-warningSoft text-warning",
  danger: "bg-dangerSoft text-danger",
  success: "bg-[#e3f4ea] text-[#137547]",
};

export function StatusBadge({ tone, children }: StatusBadgeProps) {
  return (
    <span className={cn("inline-flex rounded-full px-2.5 py-1 text-xs font-semibold uppercase tracking-wide", toneClasses[tone])}>
      {children.split("_").join(" ")}
    </span>
  );
}
