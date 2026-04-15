import type { PropsWithChildren, ReactNode } from "react";

import { cn } from "@/lib/cn";

interface CardProps extends PropsWithChildren {
  title?: ReactNode;
  description?: ReactNode;
  action?: ReactNode;
  className?: string;
}

export function Card({ title, description, action, className, children }: CardProps) {
  return (
    <section className={cn("panel", className)}>
      {(title || description || action) && (
        <div className="panel-header">
          <div>
            {title ? <h2 className="text-base font-semibold text-ink">{title}</h2> : null}
            {description ? <p className="mt-1 text-sm text-slate">{description}</p> : null}
          </div>
          {action}
        </div>
      )}
      <div className="panel-body">{children}</div>
    </section>
  );
}
