import { humanize } from "@/utils/format";

export type BadgeTone = "neutral" | "success" | "warning" | "danger" | "info";

const toneClassName: Record<BadgeTone, string> = {
  neutral: "border-line bg-surface text-ink",
  success: "border-teal/20 bg-tealSoft text-teal",
  warning: "border-amber/20 bg-amberSoft text-amber",
  danger: "border-red/20 bg-redSoft text-red",
  info: "border-blue/20 bg-blueSoft text-blue",
};

interface StatusBadgeProps {
  label: string;
  tone?: BadgeTone;
  title?: string;
}

export function StatusBadge({ label, tone = "neutral", title }: StatusBadgeProps) {
  return (
    <span
      title={title}
      className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold leading-none ${toneClassName[tone]}`}
    >
      {humanize(label)}
    </span>
  );
}
