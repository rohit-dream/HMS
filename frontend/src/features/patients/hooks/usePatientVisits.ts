import { useQuery } from "@tanstack/react-query";
import { listPatientVisitsRequest } from "@/api/endpoints/patients";

export function usePatientVisits(patientId: string | undefined, page: number, pageSize = 10) {
  return useQuery({
    queryKey: ["patients", patientId, "visits", page, pageSize],
    queryFn: () => listPatientVisitsRequest(patientId!, { page, page_size: pageSize }),
    enabled: Boolean(patientId),
  });
}
