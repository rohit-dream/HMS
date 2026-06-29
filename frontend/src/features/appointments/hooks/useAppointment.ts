import { useQuery } from "@tanstack/react-query";
import { getAppointmentRequest } from "@/api/endpoints/appointments";

export function useAppointment(appointmentId: string | undefined) {
  return useQuery({
    queryKey: ["appointments", appointmentId],
    queryFn: () => getAppointmentRequest(appointmentId!),
    enabled: Boolean(appointmentId),
  });
}
