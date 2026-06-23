import { del, get, getPaginated, patch, post } from "@/api/client";
import type { Department, DepartmentCreate, DepartmentUpdate } from "@/api/types/departments";

export async function listDepartmentsRequest(params: {
  q?: string;
  is_active?: boolean;
  location_id?: string;
  page?: number;
  page_size?: number;
}) {
  return getPaginated<Department>("/admin/departments", { params });
}

export async function getDepartmentRequest(departmentId: string): Promise<Department> {
  return get<Department>(`/admin/departments/${departmentId}`);
}

export async function createDepartmentRequest(payload: DepartmentCreate): Promise<Department> {
  return post<Department>("/admin/departments", payload);
}

export async function updateDepartmentRequest(
  departmentId: string,
  payload: DepartmentUpdate,
): Promise<Department> {
  return patch<Department>(`/admin/departments/${departmentId}`, payload);
}

export async function deleteDepartmentRequest(departmentId: string): Promise<Department> {
  return del<Department>(`/admin/departments/${departmentId}`);
}
