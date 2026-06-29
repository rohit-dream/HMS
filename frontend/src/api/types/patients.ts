export type PatientGender = "male" | "female" | "other";

export type ConsentMethod = "written" | "verbal" | "digital";

export interface PatientListItem {
  id: string;
  mrn: string;
  first_name: string;
  last_name: string | null;
  date_of_birth: string;
  gender: PatientGender;
  phone: string;
  email: string | null;
  blood_group: string | null;
  last_visit_date: string | null;
  created_at: string;
}

export interface PatientDetail extends PatientListItem {
  tenant_id: string;
  address_line1: string | null;
  city: string | null;
  state: string | null;
  postal_code: string | null;
  photo_url: string | null;
  id_proof_type: string | null;
  id_proof_number: string | null;
  marital_status: string | null;
  occupation: string | null;
  consent_given_at: string | null;
  consent_method: ConsentMethod | null;
  location_id: string | null;
  chronic_conditions: PatientChronicCondition[];
  allergies: PatientAllergy[];
  contacts: PatientContact[];
  version: number;
  updated_at: string | null;
}

export type AllergySeverity = "mild" | "moderate" | "severe";

export interface PatientAllergy {
  id: string;
  patient_id: string;
  allergen: string;
  severity: AllergySeverity;
  reaction: string | null;
  onset_date: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface PatientAllergyCreate {
  allergen: string;
  severity: AllergySeverity;
  reaction?: string;
  onset_date?: string;
  is_active?: boolean;
}

export interface PatientContact {
  id: string;
  patient_id: string;
  name: string;
  relationship: string;
  phone: string;
  email: string | null;
  is_emergency: boolean;
  is_primary: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface PatientContactCreate {
  name: string;
  relationship: string;
  phone: string;
  email?: string;
  is_emergency?: boolean;
  is_primary?: boolean;
}

export type ChronicConditionStatus = "active" | "resolved" | "inactive";

export interface PatientChronicCondition {
  id: string;
  condition_name: string;
  icd_code: string | null;
  diagnosed_date: string | null;
  status: ChronicConditionStatus;
  notes: string | null;
  recorded_at: string;
}

export interface PatientChronicConditionCreate {
  condition_name: string;
  icd_code?: string;
  diagnosed_date?: string;
  status?: ChronicConditionStatus;
  notes?: string;
}

export interface PatientVisitHistoryItem {
  id: string;
  visit_type: "opd";
  reference_number: string;
  visit_date: string;
  status: string;
  doctor_id: string;
  doctor_name: string;
  chief_complaint: string | null;
  diagnosis: string | null;
  department_name: string | null;
}

export interface PatientCreatePayload {
  first_name: string;
  last_name?: string;
  date_of_birth: string;
  gender: PatientGender;
  phone: string;
  email?: string;
  blood_group?: string;
  address_line1?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  marital_status?: string;
  occupation?: string;
  id_proof_type?: string;
  id_proof_number?: string;
  location_id?: string;
  data_processing_consent: true;
  consent_method: ConsentMethod;
  acknowledge_duplicate?: boolean;
}

export type DuplicateMatchReason = "phone" | "name";

export interface DuplicatePatientMatch {
  patient_id: string;
  mrn: string;
  first_name: string;
  last_name: string | null;
  phone: string;
  date_of_birth: string;
  match_reasons: DuplicateMatchReason[];
}

export interface DuplicateCheckResult {
  has_duplicates: boolean;
  matches: DuplicatePatientMatch[];
}
