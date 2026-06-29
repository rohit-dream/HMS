import { z } from "zod";

export const appointmentBookingSchema = z.object({
  patient_id: z.string().min(1, "Select a patient"),
  doctor_id: z.string().min(1, "Select a doctor"),
  appointment_date: z.string().min(1, "Select a date"),
  start_time: z.string().min(1, "Select a time slot"),
  end_time: z.string().min(1, "Select a time slot"),
  appointment_type: z.enum(["new", "follow_up", "emergency"], {
    message: "Select appointment type",
  }),
  is_walk_in: z.boolean(),
  notes: z.string().trim().max(2000).optional(),
});

export type AppointmentBookingFormValues = z.infer<typeof appointmentBookingSchema>;

export function toAppointmentCreatePayload(
  values: AppointmentBookingFormValues,
  locationId?: string | null,
) {
  return {
    patient_id: values.patient_id,
    doctor_id: values.doctor_id,
    location_id: locationId ?? null,
    appointment_date: values.appointment_date,
    start_time: values.start_time,
    end_time: values.end_time,
    appointment_type: values.appointment_type,
    is_walk_in: values.is_walk_in,
    notes: values.notes?.trim() || null,
  };
}
