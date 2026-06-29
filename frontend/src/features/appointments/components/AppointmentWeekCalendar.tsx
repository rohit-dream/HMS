import { Link } from "react-router-dom";
import type { Appointment } from "@/api/types/appointments";
import { AppointmentStatusBadge } from "@/features/appointments/components/AppointmentStatusBadge";
import {
  compareTimeStrings,
  getWeekDays,
  type WeekDay,
} from "@/features/appointments/utils/weekCalendar";
import { formatTime } from "@/lib/formatters";
import { cn } from "@/lib/cn";

interface AppointmentWeekCalendarProps {
  weekAnchor: Date;
  appointments: Appointment[];
  showDoctorName: boolean;
  isLoading?: boolean;
  onBookDay?: (dateIso: string) => void;
  canBook?: boolean;
}

function groupByDate(appointments: Appointment[]): Map<string, Appointment[]> {
  const map = new Map<string, Appointment[]>();
  for (const appointment of appointments) {
    const bucket = map.get(appointment.appointment_date) ?? [];
    bucket.push(appointment);
    map.set(appointment.appointment_date, bucket);
  }
  for (const [, bucket] of map) {
    bucket.sort((a, b) => compareTimeStrings(a.start_time, b.start_time));
  }
  return map;
}

function DayColumn({
  day,
  appointments,
  showDoctorName,
  onBookDay,
  canBook,
}: {
  day: WeekDay;
  appointments: Appointment[];
  showDoctorName: boolean;
  onBookDay?: (dateIso: string) => void;
  canBook?: boolean;
}) {
  return (
    <div
      className={cn(
        "flex min-h-[12rem] flex-col rounded-xl border border-border-light bg-card/80",
        day.isToday && "border-primary/40 ring-1 ring-primary/20",
      )}
    >
      <div
        className={cn(
          "flex items-start justify-between gap-2 border-b border-border-light px-3 py-2",
          day.isToday && "bg-primary/5",
        )}
      >
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-muted">{day.shortLabel}</p>
          <p className={cn("text-sm font-semibold", day.isToday ? "text-primary" : "text-foreground")}>
            {day.date.toLocaleDateString(undefined, { month: "short", day: "numeric" })}
          </p>
        </div>
        {canBook && onBookDay && (
          <button
            type="button"
            className="text-xs font-medium text-primary hover:underline"
            onClick={() => onBookDay(day.iso)}
          >
            Book
          </button>
        )}
      </div>
      <div className="flex flex-1 flex-col gap-2 p-2">
        {appointments.length === 0 && (
          <p className="px-1 py-4 text-center text-xs text-muted">No appointments</p>
        )}
        {appointments.map((appointment) => (
          <Link
            key={appointment.id}
            to={`/appointments/${appointment.id}`}
            className="block rounded-lg border border-border-light bg-surface-secondary/80 p-2 text-left transition-colors hover:border-primary/30 hover:bg-primary/5"
          >
            <p className="text-xs font-semibold text-foreground">
              {formatTime(appointment.start_time)} – {formatTime(appointment.end_time)}
            </p>
            <p className="mt-1 truncate text-sm font-medium text-foreground">
              {appointment.patient_name}
            </p>
            {showDoctorName && (
              <p className="truncate text-xs text-muted">{appointment.doctor_name}</p>
            )}
            <div className="mt-2">
              <AppointmentStatusBadge status={appointment.status} />
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

export function AppointmentWeekCalendar({
  weekAnchor,
  appointments,
  showDoctorName,
  isLoading,
  onBookDay,
  canBook,
}: AppointmentWeekCalendarProps) {
  const days = getWeekDays(weekAnchor);
  const grouped = groupByDate(appointments);

  if (isLoading) {
    return (
      <div className="grid gap-3 lg:grid-cols-7">
        {days.map((day) => (
          <div
            key={day.iso}
            className="h-48 animate-pulse rounded-xl border border-border-light bg-surface-secondary/60"
            aria-hidden
          />
        ))}
      </div>
    );
  }

  return (
    <>
      <div className="hidden gap-3 lg:grid lg:grid-cols-7">
        {days.map((day) => (
          <DayColumn
            key={day.iso}
            day={day}
            appointments={grouped.get(day.iso) ?? []}
            showDoctorName={showDoctorName}
            onBookDay={onBookDay}
            canBook={canBook}
          />
        ))}
      </div>

      <div className="space-y-3 lg:hidden">
        {days.map((day) => (
          <DayColumn
            key={day.iso}
            day={day}
            appointments={grouped.get(day.iso) ?? []}
            showDoctorName={showDoctorName}
            onBookDay={onBookDay}
            canBook={canBook}
          />
        ))}
      </div>
    </>
  );
}
