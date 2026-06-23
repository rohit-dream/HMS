export interface DoctorSchedule {
  id: string;
  tenant_id: string;
  doctor_id: string;
  day_of_week: number;
  start_time: string;
  end_time: string;
  slot_duration_minutes: number;
  max_patients_per_slot: number;
  location_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface DoctorScheduleCreate {
  day_of_week: number;
  start_time: string;
  end_time: string;
  slot_duration_minutes: number;
  max_patients_per_slot?: number;
  location_id?: string;
  is_active?: boolean;
}

export interface DoctorScheduleUpdate {
  day_of_week?: number;
  start_time?: string;
  end_time?: string;
  slot_duration_minutes?: number;
  max_patients_per_slot?: number;
  location_id?: string | null;
  is_active?: boolean;
}

export const DAY_LABELS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"] as const;

export const SLOT_DURATION_OPTIONS = [10, 15, 20, 30, 60] as const;
