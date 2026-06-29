import { useQuery } from "@tanstack/react-query";
import { getOpdVisitRequest } from "@/api/endpoints/opd";

export function useOpdVisit(visitId: string | undefined) {
  return useQuery({
    queryKey: ["opd", "visit", visitId],
    queryFn: () => getOpdVisitRequest(visitId!),
    enabled: Boolean(visitId),
  });
}
