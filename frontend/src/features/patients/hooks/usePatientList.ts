import { useQuery } from "@tanstack/react-query";
import { listPatientsRequest } from "@/api/endpoints/patients";

export function usePatientList(params: {
  search?: string;
  locationId?: string;
  page: number;
  pageSize: number;
}) {
  const { search, locationId, page, pageSize } = params;

  return useQuery({
    queryKey: ["patients", search ?? "", locationId ?? "", page, pageSize],
    queryFn: () =>
      listPatientsRequest({
        search: search || undefined,
        location_id: locationId,
        page,
        page_size: pageSize,
      }),
  });
}
