import { del, get, getPaginated, patch, post } from "@/api/client";
import type {
  DoctorSchedule,
  DoctorScheduleCreate,
  DoctorScheduleUpdate,
} from "@/api/types/doctor-schedules";

export async function listDoctorSchedulesRequest(
  doctorId: string,
  params?: {
    day_of_week?: number;
    is_active?: boolean;
    page?: number;
    page_size?: number;
  },
) {
  return getPaginated<DoctorSchedule>(`/doctors/${doctorId}/schedules`, { params });
}

export async function getDoctorScheduleRequest(
  doctorId: string,
  scheduleId: string,
): Promise<DoctorSchedule> {
  return get<DoctorSchedule>(`/doctors/${doctorId}/schedules/${scheduleId}`);
}

export async function createDoctorScheduleRequest(
  doctorId: string,
  payload: DoctorScheduleCreate,
): Promise<DoctorSchedule> {
  return post<DoctorSchedule>(`/doctors/${doctorId}/schedules`, payload);
}

export async function updateDoctorScheduleRequest(
  doctorId: string,
  scheduleId: string,
  payload: DoctorScheduleUpdate,
): Promise<DoctorSchedule> {
  return patch<DoctorSchedule>(`/doctors/${doctorId}/schedules/${scheduleId}`, payload);
}

export async function deleteDoctorScheduleRequest(
  doctorId: string,
  scheduleId: string,
): Promise<DoctorSchedule> {
  return del<DoctorSchedule>(`/doctors/${doctorId}/schedules/${scheduleId}`);
}
