import type { OpdQueuePriority, OpdQueueStatus } from "@/api/types/opd";

const QUEUE_STATUS_LABELS: Record<OpdQueueStatus, string> = {
  waiting: "Waiting",
  called: "Called",
  in_consultation: "In consultation",
  completed: "Completed",
  skipped: "Skipped",
};

const QUEUE_PRIORITY_LABELS: Record<OpdQueuePriority, string> = {
  normal: "Normal",
  urgent: "Urgent",
  emergency: "Emergency",
};

export function opdQueueStatusLabel(status: OpdQueueStatus): string {
  return QUEUE_STATUS_LABELS[status];
}

export function opdQueuePriorityLabel(priority: OpdQueuePriority): string {
  return QUEUE_PRIORITY_LABELS[priority];
}
