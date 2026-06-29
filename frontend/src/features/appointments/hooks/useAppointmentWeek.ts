import { useQuery } from "@tanstack/react-query";
import { listAppointmentsRequest } from "@/api/endpoints/appointments";

export function useAppointmentWeek(params: {
  fromDate: string;
  toDate: string;
  doctorId?: string;
}) {
  const { fromDate, toDate, doctorId } = params;

  return useQuery({
    queryKey: ["appointments", "week", fromDate, toDate, doctorId ?? "all"],
    queryFn: () =>
      listAppointmentsRequest({
        from_date: fromDate,
        to_date: toDate,
        doctor_id: doctorId,
        page: 1,
        page_size: 200,
      }),
  });
}
