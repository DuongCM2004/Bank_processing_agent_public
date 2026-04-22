type FrontendEnvironment = "local" | "test" | "development" | "staging" | "production";

function readBoolean(value: string | undefined, fallback = false) {
  if (value === undefined) {
    return fallback;
  }

  return value.toLowerCase() === "true";
}

function readNumber(value: string | undefined, fallback: number) {
  if (value === undefined) {
    return fallback;
  }

  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export const frontendConfig = {
  appName: import.meta.env.VITE_OPS_AGENT_APP_NAME ?? "Ops Agent",
  env: (import.meta.env.VITE_OPS_AGENT_ENV ?? "local") as FrontendEnvironment,
  apiBaseUrl: (
    import.meta.env.VITE_OPS_AGENT_API_BASE_URL ??
    import.meta.env.VITE_API_BASE_URL ??
    "/api/v1"
  ).replace(/\/$/, ""),
  enableMockApi: readBoolean(import.meta.env.VITE_OPS_AGENT_ENABLE_MOCK_API),
  apiTimeoutMs: readNumber(import.meta.env.VITE_OPS_AGENT_API_TIMEOUT_MS, 8_000),
  devAuth: {
    userId: import.meta.env.VITE_OPS_AGENT_DEV_USER_ID ?? "local-admin",
    roles: import.meta.env.VITE_OPS_AGENT_DEV_ROLES ?? "admin",
    displayName: import.meta.env.VITE_OPS_AGENT_DEV_DISPLAY_NAME ?? "Local Admin",
  },
};
