import { deleteNoContent, get, getPaginated, post } from "@/api/client";
import type {
  DuplicateCheckResult,
  PatientAllergy,
  PatientAllergyCreate,
  PatientChronicCondition,
  PatientChronicConditionCreate,
  PatientContact,
  PatientContactCreate,
  PatientCreatePayload,
  PatientDetail,
  PatientListItem,
  PatientVisitHistoryItem,
} from "@/api/types/patients";

export async function listPatientsRequest(params: {
  search?: string;
  location_id?: string;
  page?: number;
  page_size?: number;
}) {
  return getPaginated<PatientListItem>("/patients", { params });
}

export async function getPatientRequest(patientId: string): Promise<PatientDetail> {
  return get<PatientDetail>(`/patients/${patientId}`);
}

export async function createPatientRequest(payload: PatientCreatePayload): Promise<PatientDetail> {
  return post<PatientDetail>("/patients", payload);
}

export async function checkDuplicatePatientsRequest(params: {
  phone?: string;
  first_name?: string;
  last_name?: string;
  exclude_patient_id?: string;
}): Promise<DuplicateCheckResult> {
  return get<DuplicateCheckResult>("/patients/check-duplicate", { params });
}

export async function listPatientVisitsRequest(
  patientId: string,
  params: { page?: number; page_size?: number },
) {
  return getPaginated<PatientVisitHistoryItem>(`/patients/${patientId}/visits`, { params });
}

export async function addPatientAllergyRequest(
  patientId: string,
  payload: PatientAllergyCreate,
): Promise<PatientAllergy> {
  return post<PatientAllergy>(`/patients/${patientId}/allergies`, payload);
}

export async function deletePatientAllergyRequest(
  patientId: string,
  allergyId: string,
): Promise<void> {
  await deleteNoContent(`/patients/${patientId}/allergies/${allergyId}`);
}

export async function addPatientContactRequest(
  patientId: string,
  payload: PatientContactCreate,
): Promise<PatientContact> {
  return post<PatientContact>(`/patients/${patientId}/contacts`, payload);
}

export async function addPatientChronicConditionRequest(
  patientId: string,
  payload: PatientChronicConditionCreate,
): Promise<PatientChronicCondition> {
  return post<PatientChronicCondition>(`/patients/${patientId}/chronic-conditions`, payload);
}
