import { useQuery } from "@tanstack/react-query";
import { listDoctorsRequest } from "@/api/endpoints/doctors";

export function useDoctorsForCalendar() {
  return useQuery({
    queryKey: ["doctors", "calendar"],
    queryFn: () =>
      listDoctorsRequest({
        is_available: true,
        page: 1,
        page_size: 100,
      }),
  });
}
