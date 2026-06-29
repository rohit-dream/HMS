import { useEffect, useMemo, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import type { PatientListItem } from "@/api/types/patients";
import type { Doctor } from "@/api/types/doctors";
import { ApiError } from "@/api/errors";
import { Alert, Button, FieldLabel, Input, Modal, Select, useToast } from "@/components/ui";
import { useAppointmentAvailability } from "@/features/appointments/hooks/useAppointmentAvailability";
import { useCreateAppointment } from "@/features/appointments/hooks/useCreateAppointment";
import {
  appointmentBookingSchema,
  toAppointmentCreatePayload,
} from "@/features/appointments/schemas/appointmentBookingSchema";
import { usePatientList } from "@/features/patients/hooks/usePatientList";
import { formatPatientName, formatPhone, formatTime } from "@/lib/formatters";
import { cn } from "@/lib/cn";

export interface AppointmentBookingDefaults {
  doctorId?: string;
  appointmentDate?: string;
}

interface AppointmentBookingModalProps {
  open: boolean;
  onClose: () => void;
  doctors: Doctor[];
  defaults?: AppointmentBookingDefaults;
}

function todayIso(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function AppointmentBookingModal({
  open,
  onClose,
  doctors,
  defaults,
}: AppointmentBookingModalProps) {
  const navigate = useNavigate();
  const toast = useToast();
  const createMutation = useCreateAppointment();

  const [patientSearch, setPatientSearch] = useState("");
  const [patientQuery, setPatientQuery] = useState("");
  const [selectedPatient, setSelectedPatient] = useState<PatientListItem | null>(null);
  const [doctorId, setDoctorId] = useState("");
  const [appointmentDate, setAppointmentDate] = useState(todayIso());
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [appointmentType, setAppointmentType] = useState<"new" | "follow_up" | "emergency">("new");
  const [isWalkIn, setIsWalkIn] = useState(false);
  const [notes, setNotes] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const patientsQuery = usePatientList({
    search: patientQuery,
    page: 1,
    pageSize: 8,
  });

  const availabilityQuery = useAppointmentAvailability({
    doctorId,
    date: appointmentDate,
    enabled: open,
  });

  const availableSlots = useMemo(
    () => availabilityQuery.data?.slots.filter((slot) => slot.available) ?? [],
    [availabilityQuery.data?.slots],
  );

  useEffect(() => {
    if (!open) return;
    setDoctorId(defaults?.doctorId ?? "");
    setAppointmentDate(defaults?.appointmentDate ?? todayIso());
    setStartTime("");
    setEndTime("");
    setPatientSearch("");
    setPatientQuery("");
    setSelectedPatient(null);
    setAppointmentType("new");
    setIsWalkIn(false);
    setNotes("");
    setFormError(null);
    setFieldErrors({});
  }, [open, defaults?.doctorId, defaults?.appointmentDate]);

  function handlePatientSearchSubmit() {
    const trimmed = patientSearch.trim();
    if (trimmed.length < 2) {
      setFieldErrors((current) => ({
        ...current,
        patient_id: "Enter at least 2 characters to search patients.",
      }));
      return;
    }
    setFieldErrors((current) => {
      const next = { ...current };
      delete next.patient_id;
      return next;
    });
    setPatientQuery(trimmed);
  }

  function handleSelectPatient(patient: PatientListItem) {
    setSelectedPatient(patient);
    setPatientSearch(formatPatientName(patient.first_name, patient.last_name));
    setPatientQuery("");
    setFieldErrors((current) => {
      const next = { ...current };
      delete next.patient_id;
      return next;
    });
  }

  function handleSelectSlot(start: string, end: string) {
    setStartTime(start);
    setEndTime(end);
    setFieldErrors((current) => {
      const next = { ...current };
      delete next.start_time;
      delete next.end_time;
      return next;
    });
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setFormError(null);

    const parsed = appointmentBookingSchema.safeParse({
      patient_id: selectedPatient?.id ?? "",
      doctor_id: doctorId,
      appointment_date: appointmentDate,
      start_time: startTime,
      end_time: endTime,
      appointment_type: appointmentType,
      is_walk_in: isWalkIn,
      notes,
    });

    if (!parsed.success) {
      const errors: Record<string, string> = {};
      for (const issue of parsed.error.issues) {
        const key = String(issue.path[0] ?? "form");
        if (!errors[key]) errors[key] = issue.message;
      }
      setFieldErrors(errors);
      return;
    }

    setFieldErrors({});

    try {
      const created = await createMutation.mutateAsync(toAppointmentCreatePayload(parsed.data));
      toast.success("Appointment booked successfully.");
      onClose();
      navigate(`/appointments/${created.id}`);
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.message
          : "Unable to book appointment. Please try again.";
      setFormError(message);
    }
  }

  const patients = patientQuery.length >= 2 ? (patientsQuery.data?.data ?? []) : [];

  return (
    <Modal open={open} onClose={onClose} title="Book appointment" className="max-w-2xl">
      <form onSubmit={handleSubmit} className="space-y-5">
        <p className="text-sm text-muted">
          Select a patient, doctor, date, and an available slot from the doctor schedule.
        </p>

        {formError && <Alert variant="error">{formError}</Alert>}

        <div className="space-y-2">
          <FieldLabel htmlFor="patient-search">Patient</FieldLabel>
          <div className="flex gap-2">
            <Input
              id="patient-search"
              value={patientSearch}
              onChange={(event) => {
                setPatientSearch(event.target.value);
                if (selectedPatient) setSelectedPatient(null);
              }}
              placeholder="Search by name, phone, or MRN"
            />
            <Button type="button" variant="secondary" onClick={() => handlePatientSearchSubmit()}>
              Search
            </Button>
          </div>
          {fieldErrors.patient_id && (
            <p className="text-xs text-error">{fieldErrors.patient_id}</p>
          )}
          {selectedPatient && (
            <p className="text-sm text-foreground">
              Selected: {formatPatientName(selectedPatient.first_name, selectedPatient.last_name)} ·
              MRN {selectedPatient.mrn}
            </p>
          )}
          {patients.length > 0 && !selectedPatient && (
            <ul className="max-h-40 space-y-1 overflow-y-auto rounded-lg border border-border-light bg-surface-secondary/50 p-2">
              {patients.map((patient) => (
                <li key={patient.id}>
                  <button
                    type="button"
                    className="w-full rounded-md px-2 py-2 text-left text-sm hover:bg-primary/5"
                    onClick={() => handleSelectPatient(patient)}
                  >
                    <span className="font-medium text-foreground">
                      {formatPatientName(patient.first_name, patient.last_name)}
                    </span>
                    <span className="mt-0.5 block text-xs text-muted">
                      MRN {patient.mrn} · {formatPhone(patient.phone)}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <FieldLabel htmlFor="booking-doctor">Doctor</FieldLabel>
            <Select
              id="booking-doctor"
              value={doctorId}
              onChange={(event) => {
                setDoctorId(event.target.value);
                setStartTime("");
                setEndTime("");
              }}
            >
              <option value="">Select doctor</option>
              {doctors.map((doctor) => (
                <option key={doctor.id} value={doctor.id}>
                  Dr. {doctor.first_name} {doctor.last_name}
                </option>
              ))}
            </Select>
            {fieldErrors.doctor_id && (
              <p className="mt-1 text-xs text-error">{fieldErrors.doctor_id}</p>
            )}
          </div>

          <div>
            <FieldLabel htmlFor="booking-date">Date</FieldLabel>
            <Input
              id="booking-date"
              type="date"
              min={todayIso()}
              value={appointmentDate}
              onChange={(event) => {
                setAppointmentDate(event.target.value);
                setStartTime("");
                setEndTime("");
              }}
            />
            {fieldErrors.appointment_date && (
              <p className="mt-1 text-xs text-error">{fieldErrors.appointment_date}</p>
            )}
          </div>
        </div>

        <div>
          <FieldLabel>Available slots</FieldLabel>
          {!doctorId || !appointmentDate ? (
            <p className="text-sm text-muted">Select a doctor and date to load slots.</p>
          ) : availabilityQuery.isLoading ? (
            <p className="text-sm text-muted">Loading availability…</p>
          ) : availabilityQuery.isError ? (
            <Alert variant="error">
              {availabilityQuery.error instanceof Error
                ? availabilityQuery.error.message
                : "Unable to load availability."}
            </Alert>
          ) : availableSlots.length === 0 ? (
            <p className="text-sm text-muted">No available slots for this doctor on the selected date.</p>
          ) : (
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              {availableSlots.map((slot) => {
                const selected = startTime === slot.start_time && endTime === slot.end_time;
                return (
                  <button
                    key={`${slot.start_time}-${slot.end_time}`}
                    type="button"
                    className={cn(
                      "rounded-lg border px-3 py-2 text-sm font-medium transition-colors",
                      selected
                        ? "border-primary bg-primary/10 text-primary"
                        : "border-border-light bg-card hover:border-primary/30 hover:bg-primary/5",
                    )}
                    onClick={() => handleSelectSlot(slot.start_time, slot.end_time)}
                  >
                    {formatTime(slot.start_time)} – {formatTime(slot.end_time)}
                  </button>
                );
              })}
            </div>
          )}
          {fieldErrors.start_time && (
            <p className="mt-1 text-xs text-error">{fieldErrors.start_time}</p>
          )}
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <FieldLabel htmlFor="booking-type">Appointment type</FieldLabel>
            <Select
              id="booking-type"
              value={appointmentType}
              onChange={(event) =>
                setAppointmentType(event.target.value as "new" | "follow_up" | "emergency")
              }
            >
              <option value="new">New</option>
              <option value="follow_up">Follow-up</option>
              <option value="emergency">Emergency</option>
            </Select>
          </div>
          <div className="flex items-end">
            <label className="flex items-center gap-2 text-sm text-foreground">
              <input
                type="checkbox"
                checked={isWalkIn}
                onChange={(event) => setIsWalkIn(event.target.checked)}
              />
              Walk-in appointment
            </label>
          </div>
        </div>

        <div>
          <FieldLabel htmlFor="booking-notes">Notes (optional)</FieldLabel>
          <textarea
            id="booking-notes"
            className="glass-textarea min-h-[5rem] w-full"
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            maxLength={2000}
            placeholder="Reason for visit or front-desk notes"
          />
        </div>

        <div className="flex justify-end gap-2 border-t border-border-light pt-4">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={createMutation.isPending}>
            {createMutation.isPending ? "Booking…" : "Book appointment"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
