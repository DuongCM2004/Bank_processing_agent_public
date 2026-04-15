import type { ApiErrorEnvelope } from "@/api/contracts";
import { ApiError } from "@/api/errors";

function getApiBaseUrl() {
  return (import.meta.env.VITE_API_BASE_URL ?? "/api/v1").replace(/\/$/, "");
}

type QueryValue = string | number | boolean | null | undefined;

class ApiClient {
  constructor(private readonly baseUrl: string) {}

  async get<T>(path: string, query?: Record<string, QueryValue>) {
    const url = new URL(`${this.baseUrl}${path}`, window.location.origin);

    if (query) {
      for (const [key, value] of Object.entries(query)) {
        if (value !== undefined && value !== null && value !== "") {
          url.searchParams.set(key, String(value));
        }
      }
    }

    const response = await this.request(url.toString(), {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      await this.raiseApiError(response);
    }

    return (await response.json()) as T;
  }

  async post<TResponse, TBody extends object>(path: string, body: TBody) {
    const response = await this.request(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      await this.raiseApiError(response);
    }

    return (await response.json()) as TResponse;
  }

  private request(input: RequestInfo | URL, init: RequestInit) {
    return fetch(input, init);
  }

  private async raiseApiError(response: Response): Promise<never> {
    let payload: ApiErrorEnvelope | undefined;

    try {
      payload = (await response.json()) as ApiErrorEnvelope;
    } catch {
      payload = undefined;
    }

    if (payload?.error) {
      throw new ApiError(payload.error, response.status);
    }

    throw new ApiError(
      {
        code: "network_error",
        message: `Request failed with status ${response.status}.`,
        trace_id: null,
        details: [],
      },
      response.status,
    );
  }
}

export const apiClient = new ApiClient(getApiBaseUrl());
