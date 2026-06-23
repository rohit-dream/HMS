import axios, {
  type AxiosInstance,
  type AxiosRequestConfig,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from "axios";
import {
  clearAuthSession,
  getAccessToken,
  getTenantSlug,
  setAccessToken,
} from "@/api/auth-session";
import type { TokenResponse } from "@/api/types/auth";
import { API_BASE_URL, REQUEST_ID_HEADER, TENANT_SLUG_HEADER } from "@/lib/constants";
import { ApiError, NetworkError } from "./errors";
import type { APIResponse, PaginationMeta } from "./types";

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
  withCredentials: true,
});

let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = apiClient
      .post<APIResponse<TokenResponse>>(
        "/auth/refresh",
        {},
        {
          headers: {
            Origin: window.location.origin,
          },
        },
      )
      .then((response) => {
        const token = unwrap(response).access_token;
        setAccessToken(token);
        return token;
      })
      .catch(() => {
        clearAuthSession();
        return null;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  config.headers[REQUEST_ID_HEADER] = generateRequestId();

  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  const slug = getTenantSlug();
  if (slug) {
    config.headers[TENANT_SLUG_HEADER] = slug;
  }

  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !originalRequest.url?.includes("/auth/login") &&
      !originalRequest.url?.includes("/auth/refresh")
    ) {
      originalRequest._retry = true;
      const token = await refreshAccessToken();
      if (token) {
        originalRequest.headers.Authorization = `Bearer ${token}`;
        return apiClient(originalRequest);
      }
    }

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

export async function get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const response = await apiClient.get<APIResponse<T>>(url, config);
  return unwrap(response);
}

export async function post<T>(
  url: string,
  body?: unknown,
  config?: AxiosRequestConfig,
): Promise<T> {
  const response = await apiClient.post<APIResponse<T>>(url, body, config);
  return unwrap(response);
}

export async function patch<T>(
  url: string,
  body?: unknown,
  config?: AxiosRequestConfig,
): Promise<T> {
  const response = await apiClient.patch<APIResponse<T>>(url, body, config);
  return unwrap(response);
}

export async function put<T>(
  url: string,
  body?: unknown,
  config?: AxiosRequestConfig,
): Promise<T> {
  const response = await apiClient.put<APIResponse<T>>(url, body, config);
  return unwrap(response);
}

export async function del<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const response = await apiClient.delete<APIResponse<T>>(url, config);
  return unwrap(response);
}

export interface PaginatedResult<T> {
  data: T[];
  pagination: PaginationMeta;
}

function unwrapPaginated<T>(response: AxiosResponse<APIResponse<T[]>>): PaginatedResult<T> {
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

  if (!body.meta?.pagination) {
    throw new ApiError("Missing pagination metadata", response.status, [], requestId);
  }

  return {
    data: body.data ?? [],
    pagination: body.meta.pagination,
  };
}

export async function getPaginated<T>(
  url: string,
  config?: AxiosRequestConfig,
): Promise<PaginatedResult<T>> {
  const response = await apiClient.get<APIResponse<T[]>>(url, config);
  return unwrapPaginated(response);
}

export async function postNoContent(url: string, config?: AxiosRequestConfig): Promise<void> {
  await apiClient.post(url, undefined, config);
}
