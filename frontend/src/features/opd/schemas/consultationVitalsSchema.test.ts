import { describe, expect, it } from "vitest";
import { consultationVitalsSchema, toOpdVitalsPayload } from "./consultationVitalsSchema";

describe("consultationVitalsSchema", () => {
  it("accepts at least one vital sign", () => {
    const result = consultationVitalsSchema.safeParse({
      blood_pressure_systolic: "120",
    });
    expect(result.success).toBe(true);
  });

  it("rejects empty vitals form", () => {
    const result = consultationVitalsSchema.safeParse({});
    expect(result.success).toBe(false);
  });

  it("rejects out-of-range pulse", () => {
    const result = consultationVitalsSchema.safeParse({
      pulse_rate: "300",
    });
    expect(result.success).toBe(false);
  });

  it("maps form values to API payload", () => {
    const payload = toOpdVitalsPayload({
      pulse_rate: "72",
      temperature: "37.2",
      notes: "  Stable ",
    });
    expect(payload.pulse_rate).toBe(72);
    expect(payload.temperature).toBe(37.2);
    expect(payload.notes).toBe("Stable");
    expect(payload.spo2).toBeNull();
  });
});
