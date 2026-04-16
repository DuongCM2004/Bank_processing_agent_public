import { createContext, useContext, type PropsWithChildren } from "react";

import type { CurrentUser, OpsRole } from "@/types/roles";

const role = (import.meta.env.VITE_OPS_AGENT_USER_ROLE ?? "reviewer") as OpsRole;

const defaultUser: CurrentUser = {
  id: import.meta.env.VITE_OPS_AGENT_USER_ID ?? "local-reviewer",
  displayName: import.meta.env.VITE_OPS_AGENT_USER_NAME ?? "Local Reviewer",
  role,
};

const CurrentUserContext = createContext<CurrentUser>(defaultUser);

export function AppProviders({ children }: PropsWithChildren) {
  return <CurrentUserContext.Provider value={defaultUser}>{children}</CurrentUserContext.Provider>;
}

export function useCurrentUser() {
  return useContext(CurrentUserContext);
}
