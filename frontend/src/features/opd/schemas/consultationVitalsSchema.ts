import { z } from "zod";

const optionalInt = (min: number, max: number) =>
  z
    .union([z.string(), z.number()])
    .optional()
    .transform((value) => {
      if (value === undefined || value === null || value === "") return undefined;
      const parsed = typeof value === "number" ? value : Number.parseInt(value, 10);
      return Number.isNaN(parsed) ? undefined : parsed;
    })
    .refine((value) => value === undefined || (value >= min && value <= max), {
      message: `Must be between ${min} and ${max}`,
    });

const optionalDecimal = (min: number, max: number) =>
  z
    .union([z.string(), z.number()])
    .optional()
    .transform((value) => {
      if (value === undefined || value === null || value === "") return undefined;
      const parsed = typeof value === "number" ? value : Number.parseFloat(value);
      return Number.isNaN(parsed) ? undefined : parsed;
    })
    .refine((value) => value === undefined || (value >= min && value <= max), {
      message: `Must be between ${min} and ${max}`,
    });

export const consultationVitalsSchema = z
  .object({
    blood_pressure_systolic: optionalInt(60, 250),
    blood_pressure_diastolic: optionalInt(40, 150),
    pulse_rate: optionalInt(30, 220),
    temperature: optionalDecimal(30, 45),
    respiratory_rate: optionalInt(5, 60),
    spo2: optionalInt(50, 100),
    weight_kg: optionalDecimal(0.5, 500),
    height_cm: optionalDecimal(30, 250),
    notes: z.string().trim().max(2000).optional(),
  })
  .refine(
    (values) =>
      Object.entries(values).some(([key, value]) => {
        if (key === "notes") return typeof value === "string" && Boolean(value.trim());
        return value !== undefined;
      }),
    { message: "Enter at least one vital sign or note" },
  );

export type ConsultationVitalsFormValues = z.input<typeof consultationVitalsSchema>;

export function toOpdVitalsPayload(values: ConsultationVitalsFormValues) {
  const parsed = consultationVitalsSchema.parse(values);
  return {
    blood_pressure_systolic: parsed.blood_pressure_systolic ?? null,
    blood_pressure_diastolic: parsed.blood_pressure_diastolic ?? null,
    pulse_rate: parsed.pulse_rate ?? null,
    temperature: parsed.temperature ?? null,
    respiratory_rate: parsed.respiratory_rate ?? null,
    spo2: parsed.spo2 ?? null,
    weight_kg: parsed.weight_kg ?? null,
    height_cm: parsed.height_cm ?? null,
    notes: parsed.notes?.trim() || null,
  };
}
