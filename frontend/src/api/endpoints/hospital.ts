import { get, patch, post } from "@/api/client";
import type {
  HospitalLocation,
  HospitalProfile,
  HospitalProfileUpdate,
  LocationCreate,
  LocationUpdate,
  SettingsBulkUpdate,
  TenantSetting,
} from "@/api/types/hospital";

export async function getHospitalProfileRequest(): Promise<HospitalProfile> {
  return get<HospitalProfile>("/hospital/profile");
}

export async function updateHospitalProfileRequest(
  payload: HospitalProfileUpdate,
): Promise<HospitalProfile> {
  return patch<HospitalProfile>("/hospital/profile", payload);
}

export async function listLocationsRequest(): Promise<HospitalLocation[]> {
  return get<HospitalLocation[]>("/hospital/locations");
}

export async function createLocationRequest(payload: LocationCreate): Promise<HospitalLocation> {
  return post<HospitalLocation>("/hospital/locations", payload);
}

export async function updateLocationRequest(
  locationId: string,
  payload: LocationUpdate,
): Promise<HospitalLocation> {
  return patch<HospitalLocation>(`/hospital/locations/${locationId}`, payload);
}

export async function listSettingsRequest(): Promise<TenantSetting[]> {
  return get<TenantSetting[]>("/hospital/settings");
}

export async function bulkUpdateSettingsRequest(
  payload: SettingsBulkUpdate,
): Promise<TenantSetting[]> {
  return patch<TenantSetting[]>("/hospital/settings", payload);
}
