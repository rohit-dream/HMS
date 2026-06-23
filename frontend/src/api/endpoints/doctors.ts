import { del, get, getPaginated, patch, post } from "@/api/client";
import type { Doctor, DoctorCreate, DoctorUpdate } from "@/api/types/doctors";

export async function listDoctorsRequest(params: {
  search?: string;
  specialization?: string;
  department_id?: string;
  location_id?: string;
  is_available?: boolean;
  page?: number;
  page_size?: number;
}) {
  return getPaginated<Doctor>("/doctors", { params });
}

export async function getDoctorRequest(doctorId: string): Promise<Doctor> {
  return get<Doctor>(`/doctors/${doctorId}`);
}

export async function createDoctorRequest(payload: DoctorCreate): Promise<Doctor> {
  return post<Doctor>("/doctors", payload);
}

export async function updateDoctorRequest(
  doctorId: string,
  payload: DoctorUpdate,
): Promise<Doctor> {
  return patch<Doctor>(`/doctors/${doctorId}`, payload);
}

export async function deleteDoctorRequest(doctorId: string): Promise<Doctor> {
  return del<Doctor>(`/doctors/${doctorId}`);
}
