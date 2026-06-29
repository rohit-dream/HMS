import { useEffect, useMemo, useState } from "react";
import { RefreshCw } from "lucide-react";
import { AdminPageFrame } from "@/components/enterprise";
import { Alert, Button, FieldLabel, Select } from "@/components/ui";
import { OpdQueueBoard } from "@/features/opd/components/OpdQueueBoard";
import { useOpdQueuePoll } from "@/features/opd/hooks/useOpdQueuePoll";
import { useDoctorsForCalendar } from "@/features/appointments/hooks/useDoctorsForCalendar";
import { usePermissions } from "@/hooks/usePermissions";
import { formatPatientName } from "@/lib/formatters";

function todayIso(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function OpdQueueBoardPage() {
  const [doctorId, setDoctorId] = useState("");
  const [queueDate, setQueueDate] = useState(todayIso());

  const doctorsQuery = useDoctorsForCalendar();
  const { hasPermission } = usePermissions();
  const canManageQueue = hasPermission("opd:queue");
  const canConsult = hasPermission("opd:consult");
  const canViewQueue = hasPermission("opd:read");

  const doctors = doctorsQuery.data?.data ?? [];

  useEffect(() => {
    if (!doctorId && doctors.length > 0) {
      setDoctorId(doctors[0].id);
    }
  }, [doctorId, doctors]);

  const selectedDoctor = useMemo(
    () => doctors.find((doctor) => doctor.id === doctorId),
    [doctors, doctorId],
  );

  const pollQuery = useOpdQueuePoll({
    doctorId,
    queueDate,
    enabled: Boolean(doctorId) && canViewQueue,
  });

  return (
    <AdminPageFrame
      title="OPD Queue"
      description="Live queue board for today's outpatient consultations. Updates automatically every few seconds."
      actions={
        canViewQueue ? (
          <Button
            variant="outline"
            size="sm"
            onClick={() => pollQuery.invalidate()}
            disabled={!doctorId || pollQuery.isLoading}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh now
          </Button>
        ) : undefined
      }
    >
      <div className="flex flex-col gap-4 rounded-xl border border-border-light bg-card/60 p-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="w-full max-w-xs">
          <FieldLabel htmlFor="queue-doctor">Doctor</FieldLabel>
          <Select
            id="queue-doctor"
            value={doctorId}
            onChange={(event) => setDoctorId(event.target.value)}
            disabled={doctorsQuery.isLoading || doctors.length === 0}
          >
            <option value="">Select doctor</option>
            {doctors.map((doctor) => (
              <option key={doctor.id} value={doctor.id}>
                {formatPatientName(doctor.first_name, doctor.last_name)}
                {doctor.specialization ? ` — ${doctor.specialization}` : ""}
              </option>
            ))}
          </Select>
        </div>

        <div className="w-full max-w-xs">
          <FieldLabel htmlFor="queue-date">Queue date</FieldLabel>
          <input
            id="queue-date"
            type="date"
            value={queueDate}
            onChange={(event) => setQueueDate(event.target.value)}
            className="flex h-10 w-full rounded-lg border border-border-light bg-card px-3 text-sm text-foreground shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/30"
          />
        </div>
      </div>

      {doctorsQuery.error && (
        <Alert variant="error">Unable to load doctors. Refresh the page and try again.</Alert>
      )}

      {!canViewQueue && (
        <Alert variant="warning">
          Your account does not have permission to view the OPD queue. Ask an administrator for OPD
          read access.
        </Alert>
      )}

      {canViewQueue && pollQuery.error && (
        <Alert variant="error">
          {pollQuery.error.message || "Unable to load the queue board."}
        </Alert>
      )}

      {canViewQueue && doctorId && (
        <OpdQueueBoard
          board={pollQuery.board}
          isLoading={pollQuery.isLoading}
          canManageQueue={canManageQueue}
          canConsult={canConsult}
          onQueueChanged={pollQuery.invalidate}
        />
      )}

      {canViewQueue && !doctorId && !doctorsQuery.isLoading && (
        <Alert variant="info">Select a doctor to view today&apos;s queue.</Alert>
      )}

      {selectedDoctor && canViewQueue && pollQuery.board && (
        <p className="text-xs text-muted">
          Showing queue for {formatPatientName(selectedDoctor.first_name, selectedDoctor.last_name)}{" "}
          on {pollQuery.board.queue_date}.
        </p>
      )}
    </AdminPageFrame>
  );
}
