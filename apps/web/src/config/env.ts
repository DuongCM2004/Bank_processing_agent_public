type FrontendEnvironment = "local" | "test" | "development" | "staging" | "production";

function readBoolean(value: string | undefined, fallback = false) {
  if (value === undefined) {
    return fallback;
  }

  return value.toLowerCase() === "true";
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
};
