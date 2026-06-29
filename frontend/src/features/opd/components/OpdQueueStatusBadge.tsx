import type { OpdQueueStatus } from "@/api/types/opd";
import { Badge, type BadgeVariant } from "@/components/ui/Badge";
import { opdQueueStatusLabel } from "@/features/opd/utils/queueFormatters";

const STATUS_VARIANT: Record<OpdQueueStatus, BadgeVariant> = {
  waiting: "info",
  called: "warning",
  in_consultation: "success",
  completed: "neutral",
  skipped: "error",
};

export function OpdQueueStatusBadge({ status }: { status: OpdQueueStatus }) {
  return <Badge variant={STATUS_VARIANT[status]}>{opdQueueStatusLabel(status)}</Badge>;
}
