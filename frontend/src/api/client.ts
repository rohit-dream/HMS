import axios, { type AxiosInstance, type AxiosResponse } from "axios";
import { API_BASE_URL, REQUEST_ID_HEADER } from "@/lib/constants";
import { ApiError, NetworkError } from "./errors";
import type { APIResponse } from "./types";

function generateRequestId(): string {
  return crypto.randomUUID();
}

function unwrap<T>(response: AxiosResponse<APIResponse<T>>): T {
  const body = response.data;
  const requestId = body.meta?.request_id ?? response.headers[REQUEST_ID_HEADER.toLowerCase()];

  if (body.errors && body.errors.length > 0) {
    throw new ApiError(
      body.errors[0]?.message ?? "Request failed",
      response.status,
      body.errors,
      requestId,
    );
  }

  if (body.data === null || body.data === undefined) {
    throw new ApiError("Empty response data", response.status, [], requestId);
  }

  return body.data;
}

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    Accept: "application/json",
    "Content-Type": "application/json",
  },
  timeout: 15000,
});

apiClient.interceptors.request.use((config) => {
  config.headers[REQUEST_ID_HEADER] = generateRequestId();
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      return Promise.reject(new NetworkError());
    }

    const data = error.response.data as APIResponse<unknown> | undefined;
    if (data?.errors?.length) {
      return Promise.reject(
        new ApiError(
          data.errors[0].message,
          error.response.status,
          data.errors,
          data.meta?.request_id,
        ),
      );
    }

    return Promise.reject(
      new ApiError(
        error.message ?? "Request failed",
        error.response.status,
        [{ code: "http_error", message: String(error.response.statusText) }],
      ),
    );
  },
);

export async function get<T>(url: string): Promise<T> {
  const response = await apiClient.get<APIResponse<T>>(url);
  return unwrap(response);
}
