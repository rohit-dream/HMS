import { z } from "zod";

export const BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"] as const;

export const patientRegistrationSchema = z
  .object({
    first_name: z.string().trim().min(1, "First name is required").max(100),
    last_name: z.string().trim().max(100).optional(),
    date_of_birth: z.string().min(1, "Date of birth is required"),
    gender: z.enum(["male", "female", "other"], {
      message: "Gender is required",
    }),
    phone: z
      .string()
      .trim()
      .regex(/^\d{10}$/, "Phone must be exactly 10 digits"),
    email: z
      .string()
      .trim()
      .optional()
      .refine((value) => !value || z.string().email().safeParse(value).success, {
        message: "Enter a valid email",
      }),
    blood_group: z.enum(BLOOD_GROUPS).optional().or(z.literal("")),
    address_line1: z.string().trim().max(255).optional(),
    city: z.string().trim().max(100).optional(),
    state: z.string().trim().max(100).optional(),
    postal_code: z.string().trim().max(20).optional(),
    marital_status: z.string().trim().max(20).optional(),
    occupation: z.string().trim().max(100).optional(),
    id_proof_type: z.string().trim().max(50).optional(),
    id_proof_number: z.string().trim().max(50).optional(),
    location_id: z.string().optional(),
    consent_method: z.enum(["written", "verbal", "digital"], {
      message: "Select how consent was obtained",
    }),
    data_processing_consent: z.boolean(),
    acknowledge_duplicate: z.boolean(),
  })
  .superRefine((data, ctx) => {
    const dob = new Date(data.date_of_birth);
    if (Number.isNaN(dob.getTime())) {
      ctx.addIssue({
        code: "custom",
        message: "Enter a valid date of birth",
        path: ["date_of_birth"],
      });
    } else if (dob > new Date()) {
      ctx.addIssue({
        code: "custom",
        message: "Date of birth cannot be in the future",
        path: ["date_of_birth"],
      });
    }

    if (!data.data_processing_consent) {
      ctx.addIssue({
        code: "custom",
        message: "Patient consent is required to register",
        path: ["data_processing_consent"],
      });
    }
  });

export type PatientRegistrationFormValues = z.infer<typeof patientRegistrationSchema>;

export function toPatientCreatePayload(
  values: PatientRegistrationFormValues,
  options?: { acknowledgeDuplicate?: boolean },
) {
  return {
    first_name: values.first_name.trim(),
    last_name: values.last_name?.trim() || undefined,
    date_of_birth: values.date_of_birth,
    gender: values.gender,
    phone: values.phone.trim(),
    email: values.email?.trim() || undefined,
    blood_group: values.blood_group || undefined,
    address_line1: values.address_line1?.trim() || undefined,
    city: values.city?.trim() || undefined,
    state: values.state?.trim() || undefined,
    postal_code: values.postal_code?.trim() || undefined,
    marital_status: values.marital_status?.trim() || undefined,
    occupation: values.occupation?.trim() || undefined,
    id_proof_type: values.id_proof_type?.trim() || undefined,
    id_proof_number: values.id_proof_number?.trim() || undefined,
    location_id: values.location_id || undefined,
    data_processing_consent: true as const,
    consent_method: values.consent_method,
    acknowledge_duplicate: options?.acknowledgeDuplicate ?? values.acknowledge_duplicate,
  };
}
