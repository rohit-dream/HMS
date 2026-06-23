import { get, post } from "@/api/client";
import type {
  LegalVersions,
  TenantRegisterPayload,
  TenantRegisterResponse,
} from "@/api/types/platform";

export async function getLegalVersionsRequest(): Promise<LegalVersions> {
  return get<LegalVersions>("/platform/legal-versions");
}

export async function registerTenantRequest(
  payload: TenantRegisterPayload,
): Promise<TenantRegisterResponse> {
  return post<TenantRegisterResponse>("/platform/register", payload);
}
