import type { ApiErrorEnvelope, ApiErrorPayload } from "@/types/api";

type QueryValue = string | number | boolean | null | undefined;

export class ApiError extends Error {
  readonly status: number;
  readonly payload: ApiErrorPayload;

  constructor(payload: ApiErrorPayload, status: number) {
    super(payload.message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

const apiBaseUrl = (
  import.meta.env.VITE_OPS_AGENT_API_BASE_URL ??
  import.meta.env.VITE_API_BASE_URL ??
  "/api/v1"
).replace(/\/$/, "");

function buildUrl(path: string, query?: Record<string, QueryValue>) {
  const url = new URL(`${apiBaseUrl}${path}`, window.location.origin);

  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    }
  }

  return url;
}

async function parseError(response: Response): Promise<never> {
  let envelope: ApiErrorEnvelope | undefined;

  try {
    envelope = (await response.json()) as ApiErrorEnvelope;
  } catch {
    envelope = undefined;
  }

  throw new ApiError(
    envelope?.error ?? {
      code: "request_failed",
      message: `Request failed with status ${response.status}.`,
      trace_id: null,
      details: [],
    },
    response.status,
  );
}

export const apiClient = {
  async get<T>(path: string, query?: Record<string, QueryValue>) {
    const response = await fetch(buildUrl(path, query), {
      method: "GET",
      headers: { Accept: "application/json" },
    });

    if (!response.ok) {
      await parseError(response);
    }

    return (await response.json()) as T;
  },

  async post<TResponse, TBody extends object>(path: string, body: TBody) {
    const response = await fetch(`${apiBaseUrl}${path}`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      await parseError(response);
    }

    return (await response.json()) as TResponse;
  },
};
