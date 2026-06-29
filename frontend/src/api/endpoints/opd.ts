import { apiClient, get, patch, post } from "@/api/client";
import { ApiError } from "@/api/errors";
import { REQUEST_ID_HEADER } from "@/lib/constants";
import type { APIResponse } from "@/api/types";
import type {
  OpdClinicalNote,
  OpdNoteCreatePayload,
  OpdPrescription,
  OpdPrescriptionCreatePayload,
  OpdQueueBoard,
  OpdQueueEntry,
  OpdQueuePoll,
  OpdQueueSkipPayload,
  OpdQueueUpdatePayload,
  OpdVisitCompletePayload,
  OpdVisitCompleteResult,
  OpdVisitDetail,
  OpdVitals,
  OpdVitalsCreatePayload,
} from "@/api/types/opd";
import type { AxiosResponse } from "axios";

export type OpdQueuePollResult =
  | { kind: "not_modified"; etag: string }
  | { kind: "updated"; etag: string; data: OpdQueuePoll };

function unwrapPollBody<T>(response: AxiosResponse<APIResponse<T>>): T {
  const body = response.data;
  const requestId =
    body.meta?.request_id ??
    String(response.headers[REQUEST_ID_HEADER.toLowerCase()] ?? "");

  if (body.errors && body.errors.length > 0) {
    throw new ApiError(
      body.errors[0]?.message ?? "Request failed",
      response.status,
      body.errors,
      requestId,
    );
  }

  if (body.data === null || body.data === undefined) {
    throw new ApiError("Empty response data", response.status, [], requestId);
  }

  return body.data;
}

export function normalizeEtag(value: string | undefined | null): string | null {
  if (!value) return null;
  return value.replace(/^"|"$/g, "");
}

export async function pollOpdQueueRequest(params: {
  doctor_id: string;
  date?: string;
  location_id?: string;
  status?: string;
  ifNoneMatch?: string;
}): Promise<OpdQueuePollResult> {
  const headers: Record<string, string> = {};
  if (params.ifNoneMatch) {
    const etag = normalizeEtag(params.ifNoneMatch);
    if (etag) {
      headers["If-None-Match"] = `"${etag}"`;
    }
  }

  const response = await apiClient.get<APIResponse<OpdQueuePoll>>("/opd/queue/poll", {
    params: {
      doctor_id: params.doctor_id,
      date: params.date,
      location_id: params.location_id,
      status: params.status,
    },
    headers,
    validateStatus: (status) => status === 200 || status === 304,
  });

  const etag =
    normalizeEtag(String(response.headers.etag ?? "")) ??
    normalizeEtag(params.ifNoneMatch) ??
    "";

  if (response.status === 304) {
    return { kind: "not_modified", etag };
  }

  const data = unwrapPollBody(response);
  return {
    kind: "updated",
    etag: normalizeEtag(data.etag) ?? etag,
    data,
  };
}

export async function getOpdQueueBoardRequest(params: {
  doctor_id: string;
  date?: string;
  location_id?: string;
  status?: string;
}): Promise<OpdQueueBoard> {
  return get<OpdQueueBoard>("/opd/queue", { params });
}

export async function callOpdQueuePatientRequest(queueId: string): Promise<OpdQueueEntry> {
  return post<OpdQueueEntry>(`/opd/queue/${queueId}/call`);
}

export async function skipOpdQueuePatientRequest(
  queueId: string,
  payload: OpdQueueSkipPayload,
): Promise<OpdQueueEntry> {
  return post<OpdQueueEntry>(`/opd/queue/${queueId}/skip`, payload);
}

export async function completeOpdQueueEntryRequest(queueId: string): Promise<OpdQueueEntry> {
  return post<OpdQueueEntry>(`/opd/queue/${queueId}/complete`);
}

export async function updateOpdQueueEntryRequest(
  queueId: string,
  payload: OpdQueueUpdatePayload,
): Promise<OpdQueueEntry> {
  return patch<OpdQueueEntry>(`/opd/queue/${queueId}`, payload);
}

export async function getOpdVisitRequest(visitId: string): Promise<OpdVisitDetail> {
  return get<OpdVisitDetail>(`/opd/visits/${visitId}`);
}

export async function startOpdVisitRequest(visitId: string): Promise<OpdVisitDetail> {
  return post<OpdVisitDetail>(`/opd/visits/${visitId}/start`, {});
}

export async function completeOpdVisitRequest(
  visitId: string,
  payload?: OpdVisitCompletePayload,
): Promise<OpdVisitCompleteResult> {
  return post<OpdVisitCompleteResult>(`/opd/visits/${visitId}/complete`, payload ?? {});
}

export async function listOpdVitalsRequest(visitId: string): Promise<OpdVitals[]> {
  return get<OpdVitals[]>(`/opd/visits/${visitId}/vitals`);
}

export async function recordOpdVitalsRequest(
  visitId: string,
  payload: OpdVitalsCreatePayload,
): Promise<OpdVitals> {
  return post<OpdVitals>(`/opd/visits/${visitId}/vitals`, payload);
}

export async function listOpdNotesRequest(visitId: string): Promise<OpdClinicalNote[]> {
  return get<OpdClinicalNote[]>(`/opd/visits/${visitId}/notes`);
}

export async function createOpdNoteRequest(
  visitId: string,
  payload: OpdNoteCreatePayload,
): Promise<OpdClinicalNote> {
  return post<OpdClinicalNote>(`/opd/visits/${visitId}/notes`, payload);
}

export async function listOpdPrescriptionsRequest(visitId: string): Promise<OpdPrescription[]> {
  return get<OpdPrescription[]>(`/opd/visits/${visitId}/prescriptions`);
}

export async function createOpdPrescriptionRequest(
  visitId: string,
  payload: OpdPrescriptionCreatePayload,
): Promise<OpdPrescription> {
  return post<OpdPrescription>(`/opd/visits/${visitId}/prescriptions`, payload);
}
