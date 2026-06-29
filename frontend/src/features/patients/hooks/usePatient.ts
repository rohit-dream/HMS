import { useQuery } from "@tanstack/react-query";
import { getPatientRequest } from "@/api/endpoints/patients";

export function usePatient(patientId: string | undefined) {
  return useQuery({
    queryKey: ["patients", patientId],
    queryFn: () => getPatientRequest(patientId!),
    enabled: Boolean(patientId),
  });
}
