export type AppointmentStatus =
  | "scheduled"
  | "confirmed"
  | "completed"
  | "cancelled"
  | "no_show";

export type AppointmentType = "new" | "follow_up" | "emergency";

export interface Appointment {
  id: string;
  tenant_id: string;
  patient_id: string;
  patient_name: string;
  doctor_id: string;
  doctor_name: string;
  location_id: string | null;
  appointment_date: string;
  start_time: string;
  end_time: string;
  appointment_type: AppointmentType;
  status: AppointmentStatus;
  is_walk_in: boolean;
  notes: string | null;
  cancelled_reason: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface AvailabilitySlot {
  start_time: string;
  end_time: string;
  available: boolean;
}

export interface DoctorAvailability {
  doctor_id: string;
  date: string;
  slots: AvailabilitySlot[];
}

export interface AppointmentCancelPayload {
  cancelled_reason: string;
}

export interface AppointmentCreatePayload {
  patient_id: string;
  doctor_id: string;
  location_id?: string | null;
  appointment_date: string;
  start_time: string;
  end_time: string;
  appointment_type: AppointmentType;
  is_walk_in?: boolean;
  notes?: string | null;
}
