import { useMemo, useState } from "react";
import { CalendarPlus, ChevronLeft, ChevronRight } from "lucide-react";
import { AdminPageFrame } from "@/components/enterprise";
import { PermissionGuard } from "@/components/shared/PermissionGuard";
import { Alert, Button, FieldLabel, Select } from "@/components/ui";
import {
  AppointmentBookingModal,
  type AppointmentBookingDefaults,
} from "@/features/appointments/components/AppointmentBookingModal";
import { AppointmentWeekCalendar } from "@/features/appointments/components/AppointmentWeekCalendar";
import { useAppointmentWeek } from "@/features/appointments/hooks/useAppointmentWeek";
import { useDoctorsForCalendar } from "@/features/appointments/hooks/useDoctorsForCalendar";
import {
  addDays,
  endOfWeek,
  formatWeekRange,
  startOfWeek,
} from "@/features/appointments/utils/weekCalendar";
import { usePermissions } from "@/hooks/usePermissions";

function toIsoDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function AppointmentCalendarPage() {
  const [weekAnchor, setWeekAnchor] = useState(() => new Date());
  const [doctorId, setDoctorId] = useState("");
  const [bookingOpen, setBookingOpen] = useState(false);
  const [bookingDefaults, setBookingDefaults] = useState<AppointmentBookingDefaults>({});

  const doctorsQuery = useDoctorsForCalendar();
  const { hasPermission } = usePermissions();
  const canBook = hasPermission("appointment:create");

  const weekStart = useMemo(() => startOfWeek(weekAnchor), [weekAnchor]);
  const weekEnd = useMemo(() => endOfWeek(weekAnchor), [weekAnchor]);

  const appointmentsQuery = useAppointmentWeek({
    fromDate: toIsoDate(weekStart),
    toDate: toIsoDate(weekEnd),
    doctorId: doctorId || undefined,
  });

  const doctors = doctorsQuery.data?.data ?? [];
  const appointments = appointmentsQuery.data?.data ?? [];

  function openBookingModal(defaults?: AppointmentBookingDefaults) {
    const selectedDoctor = defaults?.doctorId ?? (doctorId || undefined);
    setBookingDefaults({
      doctorId: selectedDoctor,
      appointmentDate: defaults?.appointmentDate,
    });
    setBookingOpen(true);
  }

  return (
    <AdminPageFrame
      title="Appointments"
      description="Week view of scheduled consultations. Book new slots or open an appointment for details."
      actions={
        <PermissionGuard permission="appointment:create">
          <Button onClick={() => openBookingModal()}>
            <CalendarPlus className="mr-2 h-4 w-4" />
            Book appointment
          </Button>
        </PermissionGuard>
      }
    >
      <div className="flex flex-col gap-4 rounded-xl border border-border-light bg-card/60 p-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setWeekAnchor((current) => addDays(current, -7))}
            aria-label="Previous week"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="sm" onClick={() => setWeekAnchor(new Date())}>
            Today
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setWeekAnchor((current) => addDays(current, 7))}
            aria-label="Next week"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
          <p className="px-2 text-sm font-medium text-foreground">{formatWeekRange(weekAnchor)}</p>
        </div>

        <div className="w-full max-w-xs">
          <FieldLabel htmlFor="doctor-filter">Doctor</FieldLabel>
          <Select
            id="doctor-filter"
            value={doctorId}
            onChange={(event) => setDoctorId(event.target.value)}
          >
            <option value="">All doctors</option>
            {doctors.map((doctor) => (
              <option key={doctor.id} value={doctor.id}>
                Dr. {doctor.first_name} {doctor.last_name}
              </option>
            ))}
          </Select>
        </div>
      </div>

      {(appointmentsQuery.isError || doctorsQuery.isError) && (
        <Alert variant="error">
          {appointmentsQuery.error instanceof Error
            ? appointmentsQuery.error.message
            : doctorsQuery.error instanceof Error
              ? doctorsQuery.error.message
              : "Unable to load appointment calendar."}
        </Alert>
      )}

      <AppointmentWeekCalendar
        weekAnchor={weekAnchor}
        appointments={appointments}
        showDoctorName={!doctorId}
        isLoading={appointmentsQuery.isLoading || doctorsQuery.isLoading}
        canBook={canBook}
        onBookDay={canBook ? (dateIso) => openBookingModal({ appointmentDate: dateIso }) : undefined}
      />

      <AppointmentBookingModal
        open={bookingOpen}
        onClose={() => setBookingOpen(false)}
        doctors={doctors}
        defaults={bookingDefaults}
      />
    </AdminPageFrame>
  );
}
