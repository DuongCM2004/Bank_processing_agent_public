import type { PropsWithChildren, ReactNode } from "react";

import { useCurrentUser } from "@/app/providers";
import type { OpsRole } from "@/types/roles";

const roleRank: Record<OpsRole, number> = {
  viewer: 1,
  reviewer: 2,
  supervisor: 3,
};

interface RoleGateProps {
  minRole: OpsRole;
  fallback?: ReactNode;
}

export function RoleGate({ minRole, fallback = null, children }: PropsWithChildren<RoleGateProps>) {
  const user = useCurrentUser();
  return roleRank[user.role] >= roleRank[minRole] ? <>{children}</> : <>{fallback}</>;
}
