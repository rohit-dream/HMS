import { deleteNoContent, get, getPaginated, patch, post } from "@/api/client";
import type {
  Appointment,
  AppointmentCancelPayload,
  AppointmentCreatePayload,
  DoctorAvailability,
} from "@/api/types/appointments";

export async function listAppointmentsRequest(params: {
  doctor_id?: string;
  patient_id?: string;
  appointment_date?: string;
  from_date?: string;
  to_date?: string;
  status?: string;
  page?: number;
  page_size?: number;
}) {
  return getPaginated<Appointment>("/appointments", { params });
}

export async function getAppointmentRequest(appointmentId: string): Promise<Appointment> {
  return get<Appointment>(`/appointments/${appointmentId}`);
}

export async function createAppointmentRequest(
  payload: AppointmentCreatePayload,
): Promise<Appointment> {
  return post<Appointment>("/appointments", payload);
}

export async function confirmAppointmentRequest(appointmentId: string): Promise<Appointment> {
  return post<Appointment>(`/appointments/${appointmentId}/confirm`);
}

export async function cancelAppointmentRequest(
  appointmentId: string,
  payload: AppointmentCancelPayload,
): Promise<Appointment> {
  return post<Appointment>(`/appointments/${appointmentId}/cancel`, payload);
}

export async function getAppointmentAvailabilityRequest(params: {
  doctor_id: string;
  date: string;
  location_id?: string;
}): Promise<DoctorAvailability> {
  return get<DoctorAvailability>("/appointments/availability", { params });
}

export async function deleteAppointmentRequest(appointmentId: string): Promise<void> {
  await deleteNoContent(`/appointments/${appointmentId}`);
}

export async function updateAppointmentRequest(
  appointmentId: string,
  payload: Partial<{
    appointment_date: string;
    start_time: string;
    end_time: string;
    notes: string | null;
  }>,
): Promise<Appointment> {
  return patch<Appointment>(`/appointments/${appointmentId}`, payload);
}
