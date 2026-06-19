import type { ErrorDetail } from "./types";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly field?: string | null;
  readonly errors: ErrorDetail[];
  readonly requestId?: string;

  constructor(
    message: string,
    status: number,
    errors: ErrorDetail[] = [],
    requestId?: string,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = errors[0]?.code ?? "api_error";
    this.field = errors[0]?.field;
    this.errors = errors;
    this.requestId = requestId;
  }
}

export class NetworkError extends Error {
  constructor(message = "Network error — unable to reach API") {
    super(message);
    this.name = "NetworkError";
  }
}
