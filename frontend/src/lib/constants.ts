export const APP_NAME = import.meta.env.VITE_APP_NAME ?? "HMS Platform";
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";
export const REQUEST_ID_HEADER = "X-Request-ID";
export const TENANT_SLUG_HEADER = "X-Tenant-Slug";
export const DEFAULT_TENANT_SLUG = import.meta.env.VITE_DEFAULT_TENANT_SLUG ?? "";

const DEFAULT_SESSION_IDLE_MS = 30 * 60 * 1000;

function parseSessionIdleTimeoutMs(): number {
  const raw = import.meta.env.VITE_SESSION_IDLE_TIMEOUT_MS;
  if (raw === undefined || raw === "") {
    return DEFAULT_SESSION_IDLE_MS;
  }
  const parsed = Number(raw);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : DEFAULT_SESSION_IDLE_MS;
}

/** FR-AUTH-006 — logout after this period without user activity (configurable via env). */
export const SESSION_IDLE_TIMEOUT_MS = parseSessionIdleTimeoutMs();