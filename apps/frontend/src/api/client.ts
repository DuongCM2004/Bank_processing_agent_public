import type { ApiErrorEnvelope } from "@/api/contracts";
import { ApiError } from "@/api/errors";
import { frontendConfig } from "@/config/env";

type QueryValue = string | number | boolean | null | undefined;
interface RequestOptions {
  timeoutMs?: number;
}

class ApiClient {
  constructor(
    private readonly baseUrl: string,
    private readonly timeoutMs: number,
  ) {}

  async get<T>(path: string, query?: Record<string, QueryValue>, options?: RequestOptions) {
    const url = new URL(`${this.baseUrl}${path}`, window.location.origin);

    if (query) {
      for (const [key, value] of Object.entries(query)) {
        if (value !== undefined && value !== null && value !== "") {
          url.searchParams.set(key, String(value));
        }
      }
    }

    const response = await this.request(
      url.toString(),
      {
        method: "GET",
        headers: this.withAuthHeaders({
          Accept: "application/json",
        }),
      },
      options,
    );

    if (!response.ok) {
      await this.raiseApiError(response);
    }

    return (await response.json()) as T;
  }

  async post<TResponse, TBody extends object>(path: string, body: TBody, options?: RequestOptions) {
    const response = await this.request(
      `${this.baseUrl}${path}`,
      {
        method: "POST",
        headers: this.withAuthHeaders({
          Accept: "application/json",
          "Content-Type": "application/json",
        }),
        body: JSON.stringify(body),
      },
      options,
    );

    if (!response.ok) {
      await this.raiseApiError(response);
    }

    return (await response.json()) as TResponse;
  }

  async patch<TResponse, TBody extends object>(path: string, body: TBody, options?: RequestOptions) {
    const response = await this.request(
      `${this.baseUrl}${path}`,
      {
        method: "PATCH",
        headers: this.withAuthHeaders({
          Accept: "application/json",
          "Content-Type": "application/json",
        }),
        body: JSON.stringify(body),
      },
      options,
    );

    if (!response.ok) {
      await this.raiseApiError(response);
    }

    return (await response.json()) as TResponse;
  }

  async delete<TResponse = void>(path: string, options?: RequestOptions): Promise<TResponse | void> {
    const response = await this.request(
      `${this.baseUrl}${path}`,
      {
        method: "DELETE",
        headers: this.withAuthHeaders({
          Accept: "application/json",
        }),
      },
      options,
    );

    if (!response.ok) {
      await this.raiseApiError(response);
    }

    if (response.status === 204) {
      return;
    }

    return (await response.json()) as TResponse;
  }

  async postForm<TResponse>(path: string, body: FormData, options?: RequestOptions) {
    const response = await this.request(
      `${this.baseUrl}${path}`,
      {
        method: "POST",
        headers: this.withAuthHeaders({
          Accept: "application/json",
        }),
        body,
      },
      options,
    );

    if (!response.ok) {
      await this.raiseApiError(response);
    }

    return (await response.json()) as TResponse;
  }

  private async request(input: RequestInfo | URL, init: RequestInit, options?: RequestOptions) {
    const controller = new AbortController();
    const timeoutMs = options?.timeoutMs ?? this.timeoutMs;
    const timeout = window.setTimeout(() => controller.abort(), timeoutMs);

    try {
      return await fetch(input, {
        ...init,
        signal: controller.signal,
      });
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        throw new ApiError(
          {
            code: "request_timeout",
            message: `Request timed out after ${timeoutMs}ms.`,
            trace_id: null,
            details: [],
          },
          408,
        );
      }

      throw error;
    } finally {
      window.clearTimeout(timeout);
    }
  }

  private withAuthHeaders(headers: Record<string, string>) {
    return {
      ...headers,
      "X-Ops-Agent-User-Id": frontendConfig.devAuth.userId,
      "X-Ops-Agent-Roles": frontendConfig.devAuth.roles,
      "X-Ops-Agent-Display-Name": frontendConfig.devAuth.displayName,
    };
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

export const apiClient = new ApiClient(frontendConfig.apiBaseUrl, frontendConfig.apiTimeoutMs);
