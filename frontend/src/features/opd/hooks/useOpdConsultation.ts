import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  completeOpdVisitRequest,
  createOpdNoteRequest,
  createOpdPrescriptionRequest,
  listOpdNotesRequest,
  listOpdPrescriptionsRequest,
  listOpdVitalsRequest,
  recordOpdVitalsRequest,
  startOpdVisitRequest,
} from "@/api/endpoints/opd";
import type {
  OpdNoteCreatePayload,
  OpdPrescriptionCreatePayload,
  OpdVisitCompletePayload,
  OpdVitalsCreatePayload,
} from "@/api/types/opd";

function visitKey(visitId: string) {
  return ["opd", "visit", visitId] as const;
}

function vitalsKey(visitId: string) {
  return ["opd", "visit", visitId, "vitals"] as const;
}

function notesKey(visitId: string) {
  return ["opd", "visit", visitId, "notes"] as const;
}

function prescriptionsKey(visitId: string) {
  return ["opd", "visit", visitId, "prescriptions"] as const;
}

export function useOpdVitals(visitId: string | undefined) {
  return useQuery({
    queryKey: visitId ? vitalsKey(visitId) : ["opd", "visit", "vitals", "disabled"],
    queryFn: () => listOpdVitalsRequest(visitId!),
    enabled: Boolean(visitId),
  });
}

export function useOpdNotes(visitId: string | undefined) {
  return useQuery({
    queryKey: visitId ? notesKey(visitId) : ["opd", "visit", "notes", "disabled"],
    queryFn: () => listOpdNotesRequest(visitId!),
    enabled: Boolean(visitId),
  });
}

export function useOpdPrescriptions(visitId: string | undefined) {
  return useQuery({
    queryKey: visitId ? prescriptionsKey(visitId) : ["opd", "visit", "prescriptions", "disabled"],
    queryFn: () => listOpdPrescriptionsRequest(visitId!),
    enabled: Boolean(visitId),
  });
}

export function useOpdConsultationActions(visitId: string | undefined) {
  const queryClient = useQueryClient();

  async function invalidateAll() {
    if (!visitId) return;
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: visitKey(visitId) }),
      queryClient.invalidateQueries({ queryKey: vitalsKey(visitId) }),
      queryClient.invalidateQueries({ queryKey: notesKey(visitId) }),
      queryClient.invalidateQueries({ queryKey: prescriptionsKey(visitId) }),
    ]);
  }

  const startMutation = useMutation({
    mutationFn: () => startOpdVisitRequest(visitId!),
    onSuccess: invalidateAll,
  });

  const completeMutation = useMutation({
    mutationFn: (payload?: OpdVisitCompletePayload) =>
      completeOpdVisitRequest(visitId!, payload),
    onSuccess: invalidateAll,
  });

  const vitalsMutation = useMutation({
    mutationFn: (payload: OpdVitalsCreatePayload) =>
      recordOpdVitalsRequest(visitId!, payload),
    onSuccess: invalidateAll,
  });

  const noteMutation = useMutation({
    mutationFn: (payload: OpdNoteCreatePayload) => createOpdNoteRequest(visitId!, payload),
    onSuccess: invalidateAll,
  });

  const prescriptionMutation = useMutation({
    mutationFn: (payload: OpdPrescriptionCreatePayload) =>
      createOpdPrescriptionRequest(visitId!, payload),
    onSuccess: invalidateAll,
  });

  const isPending =
    startMutation.isPending ||
    completeMutation.isPending ||
    vitalsMutation.isPending ||
    noteMutation.isPending ||
    prescriptionMutation.isPending;

  return {
    startMutation,
    completeMutation,
    vitalsMutation,
    noteMutation,
    prescriptionMutation,
    isPending,
    invalidateAll,
  };
}
