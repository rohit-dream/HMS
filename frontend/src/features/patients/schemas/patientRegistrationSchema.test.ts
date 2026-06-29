import { describe, expect, it } from "vitest";
import {
  patientRegistrationSchema,
  toPatientCreatePayload,
} from "./patientRegistrationSchema";

const validBase = {
  first_name: "Priya",
  last_name: "Nair",
  date_of_birth: "1992-06-10",
  gender: "female" as const,
  phone: "9876012345",
  email: "",
  blood_group: "",
  consent_method: "digital" as const,
  data_processing_consent: true,
  acknowledge_duplicate: false,
};

describe("patientRegistrationSchema", () => {
  it("accepts a valid registration payload", () => {
    const result = patientRegistrationSchema.safeParse(validBase);
    expect(result.success).toBe(true);
  });

  it("rejects phone that is not 10 digits", () => {
    const result = patientRegistrationSchema.safeParse({ ...validBase, phone: "12345" });
    expect(result.success).toBe(false);
  });

  it("rejects future date of birth", () => {
    const future = new Date();
    future.setFullYear(future.getFullYear() + 1);
    const result = patientRegistrationSchema.safeParse({
      ...validBase,
      date_of_birth: future.toISOString().slice(0, 10),
    });
    expect(result.success).toBe(false);
  });

  it("requires data processing consent", () => {
    const result = patientRegistrationSchema.safeParse({
      ...validBase,
      data_processing_consent: false,
    });
    expect(result.success).toBe(false);
  });

  it("rejects invalid email", () => {
    const result = patientRegistrationSchema.safeParse({
      ...validBase,
      email: "not-an-email",
    });
    expect(result.success).toBe(false);
  });
});

describe("toPatientCreatePayload", () => {
  it("maps form values to API create body", () => {
    const parsed = patientRegistrationSchema.parse(validBase);
    const payload = toPatientCreatePayload(parsed, { acknowledgeDuplicate: true });
    expect(payload.first_name).toBe("Priya");
    expect(payload.data_processing_consent).toBe(true);
    expect(payload.consent_method).toBe("digital");
    expect(payload.acknowledge_duplicate).toBe(true);
    expect(payload.email).toBeUndefined();
  });
});
