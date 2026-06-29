import type { OpdVisitStatus } from "@/api/types/opd";
import { Badge, type BadgeVariant } from "@/components/ui";

const statusLabels: Record<OpdVisitStatus, string> = {
  waiting: "Waiting",
  in_consultation: "In consultation",
  completed: "Completed",
  cancelled: "Cancelled",
  no_show: "No show",
};

const statusVariants: Record<OpdVisitStatus, BadgeVariant> = {
  waiting: "warning",
  in_consultation: "neutral",
  completed: "success",
  cancelled: "error",
  no_show: "error",
};

export function OpdVisitStatusBadge({ status }: { status: OpdVisitStatus }) {
  return <Badge variant={statusVariants[status]}>{statusLabels[status]}</Badge>;
}
