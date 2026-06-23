/** In-memory auth state — access token must never be stored in localStorage. */

let accessToken: string | null = null;
let tenantSlug: string | null = null;

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function getTenantSlug(): string | null {
  return tenantSlug;
}

export function setTenantSlug(slug: string | null): void {
  tenantSlug = slug?.trim().toLowerCase() ?? null;
}

export function clearAuthSession(): void {
  accessToken = null;
  tenantSlug = null;
}
