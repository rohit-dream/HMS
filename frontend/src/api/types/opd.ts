export type OpdQueueStatus =
  | "waiting"
  | "called"
  | "in_consultation"
  | "completed"
  | "skipped";

export type OpdQueuePriority = "normal" | "urgent" | "emergency";

export type OpdVisitStatus =
  | "waiting"
  | "in_consultation"
  | "completed"
  | "cancelled"
  | "no_show";

export interface OpdQueueEntry {
  id: string;
  opd_visit_id: string;
  doctor_id: string;
  patient_id: string;
  patient_name: string | null;
  token_number: number;
  queue_date: string;
  status: OpdQueueStatus;
  priority: OpdQueuePriority;
  chief_complaint: string | null;
  called_at: string | null;
  visit_status: OpdVisitStatus | null;
}

export interface OpdQueueBoard {
  doctor_id: string;
  queue_date: string;
  current_token: number | null;
  waiting_count: number;
  entries: OpdQueueEntry[];
}

export interface OpdQueuePoll extends OpdQueueBoard {
  etag: string;
  poll_interval_seconds: number;
  changed: boolean;
}

export interface OpdQueueSkipPayload {
  reason: string;
}

export interface OpdQueueUpdatePayload {
  priority?: OpdQueuePriority;
  position?: number;
}

export type OpdVisitType = "walk_in" | "appointment";

export type OpdNoteType = "examination" | "diagnosis" | "plan" | "general";

export type OpdPrescriptionStatus =
  | "active"
  | "dispensed"
  | "partially_dispensed"
  | "cancelled";

export type MedicineRoute = "oral" | "topical" | "iv" | "im" | "sc" | "inhalation" | "other";

export interface OpdVisit {
  id: string;
  tenant_id: string;
  visit_number: string;
  patient_id: string;
  patient_name: string | null;
  patient_mrn: string | null;
  doctor_id: string;
  doctor_name: string | null;
  appointment_id: string | null;
  location_id: string | null;
  location_name: string | null;
  visit_date: string;
  visit_type: OpdVisitType;
  status: OpdVisitStatus;
  token_number: number | null;
  chief_complaint: string | null;
  started_at: string | null;
  completed_at: string | null;
  queue_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface OpdVisitDetail extends OpdVisit {
  vitals_count: number;
  notes_count: number;
  prescriptions_count: number;
}

export interface OpdVisitCompleteResult {
  id: string;
  status: OpdVisitStatus;
  completed_at: string;
  billing_invoice_id: string | null;
}

export interface OpdVisitCompletePayload {
  finalize_notes?: boolean;
  create_billing_draft?: boolean;
  follow_up_notes?: string | null;
}

export interface OpdVitals {
  id: string;
  opd_visit_id: string;
  recorded_at: string;
  recorded_by_user_id: string | null;
  blood_pressure_systolic: number | null;
  blood_pressure_diastolic: number | null;
  pulse_rate: number | null;
  temperature: number | null;
  temperature_unit: string | null;
  respiratory_rate: number | null;
  spo2: number | null;
  weight_kg: number | null;
  height_cm: number | null;
  bmi: number | null;
  notes: string | null;
}

export interface OpdVitalsCreatePayload {
  blood_pressure_systolic?: number | null;
  blood_pressure_diastolic?: number | null;
  pulse_rate?: number | null;
  temperature?: number | null;
  respiratory_rate?: number | null;
  spo2?: number | null;
  weight_kg?: number | null;
  height_cm?: number | null;
  notes?: string | null;
}

export interface OpdClinicalNote {
  id: string;
  opd_visit_id: string;
  note_type: OpdNoteType;
  content: string;
  icd_code: string | null;
  icd_description: string | null;
  is_final: boolean;
  created_by_user_id: string | null;
  created_at: string;
}

export interface OpdNoteCreatePayload {
  note_type: OpdNoteType;
  content: string;
  icd_code?: string | null;
  icd_description?: string | null;
}

export interface OpdPrescriptionItem {
  id: string;
  medicine_id: string | null;
  medicine_name: string;
  dosage: string;
  frequency: string;
  duration: string;
  route: MedicineRoute | null;
  instructions: string | null;
  quantity: number | null;
}

export interface OpdPrescription {
  id: string;
  opd_visit_id: string;
  patient_id: string;
  doctor_id: string;
  prescription_number: string;
  prescribed_at: string;
  status: OpdPrescriptionStatus;
  notes: string | null;
  items: OpdPrescriptionItem[];
}

export interface OpdPrescriptionItemCreatePayload {
  medicine_id?: string | null;
  medicine_name: string;
  dosage: string;
  frequency: string;
  duration: string;
  route?: MedicineRoute | null;
  instructions?: string | null;
  quantity?: number | null;
}

export interface OpdPrescriptionCreatePayload {
  notes?: string | null;
  items: OpdPrescriptionItemCreatePayload[];
}
