import type { ReactNode } from "react";

import type { UserRole } from "@/lib/types";

export function RoleGate({
  allowed,
  currentRole,
  fallback,
  children,
}: {
  allowed: UserRole[];
  currentRole: UserRole;
  fallback?: ReactNode;
  children: ReactNode;
}) {
  if (!allowed.includes(currentRole)) {
    return fallback ?? null;
  }

  return <>{children}</>;
}
