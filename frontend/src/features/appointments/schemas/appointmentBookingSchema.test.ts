import { describe, expect, it } from "vitest";
import {
  appointmentBookingSchema,
  toAppointmentCreatePayload,
} from "./appointmentBookingSchema";

const validBooking = {
  patient_id: "c3d4e5f6-a7b8-9012-cdef-123456789012",
  doctor_id: "e5f6a7b8-c9d0-1234-ef01-345678901234",
  appointment_date: "2026-06-20",
  start_time: "09:00:00",
  end_time: "09:20:00",
  appointment_type: "new" as const,
  is_walk_in: false,
  notes: "Follow-up visit",
};

describe("appointmentBookingSchema", () => {
  it("accepts a valid booking payload", () => {
    const result = appointmentBookingSchema.safeParse(validBooking);
    expect(result.success).toBe(true);
  });

  it("rejects missing patient", () => {
    const result = appointmentBookingSchema.safeParse({
      ...validBooking,
      patient_id: "",
    });
    expect(result.success).toBe(false);
  });

  it("maps form values to API payload", () => {
    const payload = toAppointmentCreatePayload(validBooking, "d4e5f6a7-b8c9-0123-def0-234567890123");
    expect(payload.patient_id).toBe(validBooking.patient_id);
    expect(payload.location_id).toBe("d4e5f6a7-b8c9-0123-def0-234567890123");
    expect(payload.notes).toBe("Follow-up visit");
  });
});
