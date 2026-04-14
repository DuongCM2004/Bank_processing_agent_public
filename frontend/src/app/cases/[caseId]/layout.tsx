import type { ReactNode } from "react";

import { AppShell } from "@/components/app-shell";
import { demoUser } from "@/lib/mock-data";

export default function CaseLayout({ children }: { children: ReactNode }) {
  return <AppShell user={demoUser}>{children}</AppShell>;
}
