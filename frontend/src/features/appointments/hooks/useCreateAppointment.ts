import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createAppointmentRequest } from "@/api/endpoints/appointments";
import type { AppointmentCreatePayload } from "@/api/types/appointments";

export function useCreateAppointment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: AppointmentCreatePayload) => createAppointmentRequest(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["appointments"] });
    },
  });
}
