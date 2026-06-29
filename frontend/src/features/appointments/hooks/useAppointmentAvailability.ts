import { useQuery } from "@tanstack/react-query";
import { getAppointmentAvailabilityRequest } from "@/api/endpoints/appointments";

export function useAppointmentAvailability(params: {
  doctorId: string;
  date: string;
  enabled?: boolean;
}) {
  const { doctorId, date, enabled = true } = params;

  return useQuery({
    queryKey: ["appointments", "availability", doctorId, date],
    queryFn: () =>
      getAppointmentAvailabilityRequest({
        doctor_id: doctorId,
        date,
      }),
    enabled: enabled && Boolean(doctorId && date),
  });
}
