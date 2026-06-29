import { useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CalendarDays, Stethoscope, UserRound } from "lucide-react";
import {
  cancelAppointmentRequest,
  confirmAppointmentRequest,
} from "@/api/endpoints/appointments";
import { ApiError } from "@/api/errors";
import { AdminPageFrame } from "@/components/enterprise";
import { PermissionGuard } from "@/components/shared/PermissionGuard";
import {
  Alert,
  Button,
  FieldLabel,
  Input,
  Modal,
  primaryLinkClassName,
  useToast,
} from "@/components/ui";
import { GlassCard } from "@/components/ui/GlassCard";
import { AppointmentStatusBadge } from "@/features/appointments/components/AppointmentStatusBadge";
import { useAppointment } from "@/features/appointments/hooks/useAppointment";
import {
  appointmentTypeLabel,
  formatDate,
  formatTime,
} from "@/lib/formatters";

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-muted">{label}</dt>
      <dd className="mt-1 font-medium text-foreground">{value}</dd>
    </div>
  );
}

export function AppointmentDetailPage() {
  const { appointmentId } = useParams<{ appointmentId: string }>();
  const queryClient = useQueryClient();
  const toast = useToast();
  const [cancelOpen, setCancelOpen] = useState(false);
  const [cancelReason, setCancelReason] = useState("");

  const appointmentQuery = useAppointment(appointmentId);
  const appointment = appointmentQuery.data;

  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ["appointments"] });
  };

  const confirmMutation = useMutation({
    mutationFn: () => confirmAppointmentRequest(appointmentId!),
    onSuccess: async () => {
      await invalidate();
      toast.success("Appointment confirmed.");
    },
    onError: (error) => {
      const message = error instanceof ApiError ? error.message : "Unable to confirm appointment.";
      toast.error(message);
    },
  });

  const cancelMutation = useMutation({
    mutationFn: (reason: string) =>
      cancelAppointmentRequest(appointmentId!, { cancelled_reason: reason }),
    onSuccess: async () => {
      await invalidate();
      setCancelOpen(false);
      setCancelReason("");
      toast.success("Appointment cancelled.");
    },
    onError: (error) => {
      const message = error instanceof ApiError ? error.message : "Unable to cancel appointment.";
      toast.error(message);
    },
  });

  function handleCancelSubmit(event: FormEvent) {
    event.preventDefault();
    const reason = cancelReason.trim();
    if (!reason) return;
    cancelMutation.mutate(reason);
  }

  const canConfirm = appointment?.status === "scheduled";
  const canCancel =
    appointment?.status === "scheduled" || appointment?.status === "confirmed";

  return (
    <AdminPageFrame
      title="Appointment details"
      description="Review booking information and update appointment status."
      actions={
        <Link to="/appointments" className={primaryLinkClassName}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to calendar
        </Link>
      }
    >
      {appointmentQuery.isLoading && (
        <GlassCard padding="lg">
          <p className="text-sm text-muted">Loading appointment…</p>
        </GlassCard>
      )}

      {appointmentQuery.isError && (
        <Alert variant="error">
          {appointmentQuery.error instanceof Error
            ? appointmentQuery.error.message
            : "Unable to load appointment."}
        </Alert>
      )}

      {appointment && (
        <div className="space-y-6">
          <GlassCard padding="lg" className="space-y-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-sm text-muted">Status</p>
                <div className="mt-2">
                  <AppointmentStatusBadge status={appointment.status} />
                </div>
              </div>
              <PermissionGuard permission="appointment:update">
                <div className="flex flex-wrap gap-2">
                  {canConfirm && (
                    <Button
                      onClick={() => confirmMutation.mutate()}
                      disabled={confirmMutation.isPending}
                    >
                      Confirm
                    </Button>
                  )}
                  {canCancel && (
                    <Button variant="danger" onClick={() => setCancelOpen(true)}>
                      Cancel appointment
                    </Button>
                  )}
                </div>
              </PermissionGuard>
            </div>

            <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <DetailRow
                label="Date"
                value={`${formatDate(appointment.appointment_date)} (${formatTime(appointment.start_time)} – ${formatTime(appointment.end_time)})`}
              />
              <DetailRow label="Type" value={appointmentTypeLabel(appointment.appointment_type)} />
              <DetailRow label="Walk-in" value={appointment.is_walk_in ? "Yes" : "No"} />
              <DetailRow label="Patient" value={appointment.patient_name} />
              <DetailRow label="Doctor" value={appointment.doctor_name} />
              <DetailRow label="Notes" value={appointment.notes?.trim() || "—"} />
              {appointment.cancelled_reason && (
                <DetailRow label="Cancellation reason" value={appointment.cancelled_reason} />
              )}
            </dl>
          </GlassCard>

          <div className="grid gap-4 sm:grid-cols-2">
            <GlassCard padding="md" className="flex items-start gap-3">
              <UserRound className="mt-0.5 h-5 w-5 text-primary" aria-hidden />
              <div>
                <p className="text-sm font-medium text-foreground">Patient</p>
                <p className="text-sm text-muted">{appointment.patient_name}</p>
                <Link
                  to={`/patients/${appointment.patient_id}`}
                  className="mt-2 inline-block text-sm text-primary hover:underline"
                >
                  View patient profile
                </Link>
              </div>
            </GlassCard>
            <GlassCard padding="md" className="flex items-start gap-3">
              <Stethoscope className="mt-0.5 h-5 w-5 text-primary" aria-hidden />
              <div>
                <p className="text-sm font-medium text-foreground">Doctor</p>
                <p className="text-sm text-muted">{appointment.doctor_name}</p>
              </div>
            </GlassCard>
            <GlassCard padding="md" className="flex items-start gap-3 sm:col-span-2">
              <CalendarDays className="mt-0.5 h-5 w-5 text-primary" aria-hidden />
              <div>
                <p className="text-sm font-medium text-foreground">Booked on</p>
                <p className="text-sm text-muted">{formatDate(appointment.created_at)}</p>
              </div>
            </GlassCard>
          </div>
        </div>
      )}

      <Modal open={cancelOpen} onClose={() => setCancelOpen(false)} title="Cancel appointment">
        <p className="mb-4 text-sm text-muted">
          Provide a reason for cancellation. This frees the doctor slot for rebooking.
        </p>
        <form onSubmit={handleCancelSubmit} className="space-y-4">
          <div>
            <FieldLabel htmlFor="cancel-reason">Cancellation reason</FieldLabel>
            <Input
              id="cancel-reason"
              value={cancelReason}
              onChange={(event) => setCancelReason(event.target.value)}
              placeholder="Patient requested cancellation"
              maxLength={500}
              required
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setCancelOpen(false)}>
              Close
            </Button>
            <Button
              type="submit"
              variant="danger"
              disabled={cancelMutation.isPending || !cancelReason.trim()}
            >
              Cancel appointment
            </Button>
          </div>
        </form>
      </Modal>
    </AdminPageFrame>
  );
}
