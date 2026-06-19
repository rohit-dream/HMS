import { get } from "@/api/client";
import type { HealthData, ReadinessData } from "@/api/types";

export function getHealth(): Promise<HealthData> {
  return get<HealthData>("/health");
}

export function getReady(): Promise<ReadinessData> {
  return get<ReadinessData>("/health/ready");
}
