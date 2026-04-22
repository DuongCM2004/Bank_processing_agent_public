import type { ApiErrorPayload } from "@/api/contracts";

export class ApiError extends Error {
  readonly code: string;
  readonly traceId: string | null;
  readonly details: ApiErrorPayload["details"];
  readonly status: number;

  constructor(payload: ApiErrorPayload, status: number) {
    super(payload.message);
    this.name = "ApiError";
    this.code = payload.code;
    this.traceId = payload.trace_id ?? null;
    this.details = payload.details;
    this.status = status;
  }
}
