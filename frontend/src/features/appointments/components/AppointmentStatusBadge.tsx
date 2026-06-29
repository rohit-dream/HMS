import type { AppointmentStatus } from "@/api/types/appointments";
import { Badge, type BadgeVariant } from "@/components/ui/Badge";
import { appointmentStatusLabel } from "@/lib/formatters";

const STATUS_VARIANT: Record<AppointmentStatus, BadgeVariant> = {
  scheduled: "info",
  confirmed: "success",
  completed: "neutral",
  cancelled: "error",
  no_show: "warning",
};

export function AppointmentStatusBadge({ status }: { status: AppointmentStatus }) {
  return <Badge variant={STATUS_VARIANT[status]}>{appointmentStatusLabel(status)}</Badge>;
}
