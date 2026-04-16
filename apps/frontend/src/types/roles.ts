export type OpsRole = "viewer" | "reviewer" | "supervisor";

export interface CurrentUser {
  id: string;
  displayName: string;
  role: OpsRole;
}
