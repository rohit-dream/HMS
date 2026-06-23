import { del, get, getPaginated, patch, post } from "@/api/client";
import type { StaffCreate, StaffMember, StaffUpdate } from "@/api/types/staff";

export async function listStaffRequest(params: {
  search?: string;
  status?: string;
  department_id?: string;
  location_id?: string;
  page?: number;
  page_size?: number;
}) {
  return getPaginated<StaffMember>("/staff", { params });
}

export async function getStaffRequest(staffId: string): Promise<StaffMember> {
  return get<StaffMember>(`/staff/${staffId}`);
}

export async function createStaffRequest(payload: StaffCreate): Promise<StaffMember> {
  return post<StaffMember>("/staff", payload);
}

export async function updateStaffRequest(
  staffId: string,
  payload: StaffUpdate,
): Promise<StaffMember> {
  return patch<StaffMember>(`/staff/${staffId}`, payload);
}

export async function deleteStaffRequest(staffId: string): Promise<StaffMember> {
  return del<StaffMember>(`/staff/${staffId}`);
}
