import type { OpdVisitStatus } from "@/api/types/opd";

const visitStatusLabels: Record<string, string> = {
  waiting: "Waiting",
  in_consultation: "In consultation",
  completed: "Completed",
  cancelled: "Cancelled",
  no_show: "No show",
};

export function patientVisitStatusLabel(status: string): string {
  return visitStatusLabels[status] ?? status.replace(/_/g, " ");
}

export function isOpdVisitStatus(status: string): status is OpdVisitStatus {
  return status in visitStatusLabels;
}

export function truncateText(value: string | null | undefined, maxLength = 80): string {
  if (!value?.trim()) return "—";
  const trimmed = value.trim();
  if (trimmed.length <= maxLength) return trimmed;
  return `${trimmed.slice(0, maxLength - 1)}…`;
}
