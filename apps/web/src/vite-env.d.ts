/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_OPS_AGENT_APP_NAME?: string;
  readonly VITE_OPS_AGENT_ENV?: "local" | "test" | "development" | "staging" | "production";
  readonly VITE_OPS_AGENT_API_BASE_URL?: string;
  readonly VITE_OPS_AGENT_ENABLE_MOCK_API?: string;
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
