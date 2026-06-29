import { useMutation } from "@tanstack/react-query";
import {
  callOpdQueuePatientRequest,
  completeOpdQueueEntryRequest,
  skipOpdQueuePatientRequest,
  updateOpdQueueEntryRequest,
} from "@/api/endpoints/opd";
import type { OpdQueueSkipPayload, OpdQueueUpdatePayload } from "@/api/types/opd";

export function useOpdQueueActions(onSuccess?: () => void) {
  const callMutation = useMutation({
    mutationFn: (queueId: string) => callOpdQueuePatientRequest(queueId),
    onSuccess,
  });

  const skipMutation = useMutation({
    mutationFn: ({ queueId, payload }: { queueId: string; payload: OpdQueueSkipPayload }) =>
      skipOpdQueuePatientRequest(queueId, payload),
    onSuccess,
  });

  const completeMutation = useMutation({
    mutationFn: (queueId: string) => completeOpdQueueEntryRequest(queueId),
    onSuccess,
  });

  const reorderMutation = useMutation({
    mutationFn: ({ queueId, payload }: { queueId: string; payload: OpdQueueUpdatePayload }) =>
      updateOpdQueueEntryRequest(queueId, payload),
    onSuccess,
  });

  return {
    callMutation,
    skipMutation,
    completeMutation,
    reorderMutation,
    isPending:
      callMutation.isPending ||
      skipMutation.isPending ||
      completeMutation.isPending ||
      reorderMutation.isPending,
  };
}
