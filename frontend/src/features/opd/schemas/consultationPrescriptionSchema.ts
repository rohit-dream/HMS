import { z } from "zod";

export const prescriptionItemSchema = z.object({
  medicine_name: z.string().trim().min(1, "Drug name is required").max(255),
  dosage: z.string().trim().min(1, "Dosage is required").max(100),
  frequency: z.string().trim().min(1, "Frequency is required").max(100),
  duration: z.string().trim().min(1, "Duration is required").max(100),
  route: z
    .enum(["oral", "topical", "iv", "im", "sc", "inhalation", "other"])
    .optional()
    .default("oral"),
  instructions: z.string().trim().max(2000).optional(),
  quantity: z
    .union([z.string(), z.number()])
    .optional()
    .transform((value) => {
      if (value === undefined || value === null || value === "") return undefined;
      const parsed = typeof value === "number" ? value : Number.parseInt(value, 10);
      return Number.isNaN(parsed) ? undefined : parsed;
    })
    .refine((value) => value === undefined || value >= 1, {
      message: "Quantity must be at least 1",
    }),
});

export const consultationPrescriptionSchema = z.object({
  notes: z.string().trim().max(2000).optional(),
  items: z.array(prescriptionItemSchema).min(1, "Add at least one medication"),
});

export type PrescriptionItemFormValues = z.input<typeof prescriptionItemSchema>;
export type ConsultationPrescriptionFormValues = z.input<typeof consultationPrescriptionSchema>;

export function emptyPrescriptionItem(): PrescriptionItemFormValues {
  return {
    medicine_name: "",
    dosage: "",
    frequency: "",
    duration: "",
    route: "oral",
    instructions: "",
    quantity: "",
  };
}

export function toOpdPrescriptionPayload(values: ConsultationPrescriptionFormValues) {
  const parsed = consultationPrescriptionSchema.parse(values);
  return {
    notes: parsed.notes?.trim() || null,
    items: parsed.items.map((item) => ({
      medicine_name: item.medicine_name.trim(),
      dosage: item.dosage.trim(),
      frequency: item.frequency.trim(),
      duration: item.duration.trim(),
      route: item.route ?? "oral",
      instructions: item.instructions?.trim() || null,
      quantity: item.quantity ?? null,
    })),
  };
}
