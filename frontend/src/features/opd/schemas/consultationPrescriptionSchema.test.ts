import { describe, expect, it } from "vitest";
import {
  consultationPrescriptionSchema,
  toOpdPrescriptionPayload,
} from "./consultationPrescriptionSchema";

const validItem = {
  medicine_name: "Paracetamol",
  dosage: "500 mg",
  frequency: "Twice daily",
  duration: "5 days",
  route: "oral" as const,
  instructions: "After meals",
  quantity: "10",
};

describe("consultationPrescriptionSchema", () => {
  it("accepts a valid prescription", () => {
    const result = consultationPrescriptionSchema.safeParse({
      notes: "Take with food",
      items: [validItem],
    });
    expect(result.success).toBe(true);
  });

  it("rejects missing drug name", () => {
    const result = consultationPrescriptionSchema.safeParse({
      items: [{ ...validItem, medicine_name: "" }],
    });
    expect(result.success).toBe(false);
  });

  it("maps form values to API payload", () => {
    const payload = toOpdPrescriptionPayload({
      notes: "  Hydrate well ",
      items: [validItem],
    });
    expect(payload.notes).toBe("Hydrate well");
    expect(payload.items[0]?.medicine_name).toBe("Paracetamol");
    expect(payload.items[0]?.quantity).toBe(10);
    expect(payload.items[0]?.route).toBe("oral");
  });
});
