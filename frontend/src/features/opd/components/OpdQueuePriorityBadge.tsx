import type { OpdQueuePriority } from "@/api/types/opd";
import { Badge, type BadgeVariant } from "@/components/ui/Badge";
import { opdQueuePriorityLabel } from "@/features/opd/utils/queueFormatters";

const PRIORITY_VARIANT: Record<OpdQueuePriority, BadgeVariant> = {
  normal: "neutral",
  urgent: "warning",
  emergency: "error",
};

export function OpdQueuePriorityBadge({ priority }: { priority: OpdQueuePriority }) {
  return <Badge variant={PRIORITY_VARIANT[priority]}>{opdQueuePriorityLabel(priority)}</Badge>;
}
