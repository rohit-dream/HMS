import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  checkDuplicatePatientsRequest,
  createPatientRequest,
} from "@/api/endpoints/patients";
import { listLocationsRequest } from "@/api/endpoints/hospital";
import { ApiError } from "@/api/errors";
import { FormField } from "@/components/forms/FormField";
import { AdminPageFrame, FormHelpCard, FormPageLayout, FormSection } from "@/components/enterprise";
import { DuplicatePatientAlert } from "@/features/patients/components/DuplicatePatientAlert";
import {
  BLOOD_GROUPS,
  patientRegistrationSchema,
  toPatientCreatePayload,
  type PatientRegistrationFormValues,
} from "@/features/patients/schemas/patientRegistrationSchema";
import { Alert, Button, primaryLinkClassName } from "@/components/ui";

const defaultValues: PatientRegistrationFormValues = {
  first_name: "",
  last_name: "",
  date_of_birth: "",
  gender: "female",
  phone: "",
  email: "",
  blood_group: "",
  address_line1: "",
  city: "",
  state: "",
  postal_code: "",
  marital_status: "",
  occupation: "",
  id_proof_type: "",
  id_proof_number: "",
  location_id: "",
  consent_method: "digital",
  data_processing_consent: false,
  acknowledge_duplicate: false,
};

export function PatientRegistrationPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [submitError, setSubmitError] = useState<string | null>(null);

  const form = useForm<PatientRegistrationFormValues>({
    resolver: zodResolver(patientRegistrationSchema),
    defaultValues,
  });

  const phone = form.watch("phone");
  const firstName = form.watch("first_name");
  const lastName = form.watch("last_name");
  const acknowledgeDuplicate = form.watch("acknowledge_duplicate");

  const phoneDigits = phone.replace(/\D/g, "");
  const canCheckDuplicates =
    phoneDigits.length === 10 || firstName.trim().length >= 2;

  const duplicateQuery = useQuery({
    queryKey: ["patients", "check-duplicate", phoneDigits, firstName.trim(), lastName?.trim() ?? ""],
    queryFn: () =>
      checkDuplicatePatientsRequest({
        phone: phoneDigits.length === 10 ? phoneDigits : undefined,
        first_name: firstName.trim().length >= 2 ? firstName.trim() : undefined,
        last_name: lastName?.trim() || undefined,
      }),
    enabled: canCheckDuplicates,
    staleTime: 30_000,
  });

  const locationsQuery = useQuery({
    queryKey: ["hospital", "locations"],
    queryFn: listLocationsRequest,
  });

  useEffect(() => {
    if (!duplicateQuery.data?.has_duplicates) {
      form.setValue("acknowledge_duplicate", false);
    }
  }, [duplicateQuery.data?.has_duplicates, form]);

  const createMutation = useMutation({
    mutationFn: createPatientRequest,
    onSuccess: async (patient) => {
      await queryClient.invalidateQueries({ queryKey: ["patients"] });
      navigate(`/patients/${patient.id}`);
    },
    onError: (error) => {
      if (error instanceof ApiError) {
        if (error.status === 402) {
          setSubmitError(
            error.message ||
              "Trial patient limit reached. Upgrade your plan to register more patients.",
          );
          return;
        }
        if (error.status === 409) {
          setSubmitError(
            "A patient with this phone number already exists. Review duplicates and confirm to proceed.",
          );
          return;
        }
        setSubmitError(error.message);
        return;
      }
      setSubmitError("Unable to register patient. Please try again.");
    },
  });

  function onSubmit(values: PatientRegistrationFormValues) {
    setSubmitError(null);

    if (duplicateQuery.data?.has_duplicates && !values.acknowledge_duplicate) {
      form.setError("acknowledge_duplicate", {
        message: "Confirm duplicate review to continue",
      });
      return;
    }

    createMutation.mutate(toPatientCreatePayload(values));
  }

  const duplicateMatches = duplicateQuery.data?.matches ?? [];
  const locations = locationsQuery.data ?? [];
  const saving = createMutation.isPending;

  return (
    <AdminPageFrame
      title="Register patient"
      description="Capture demographics, contact details, and data-processing consent for a new patient record."
      actions={
        <Link to="/patients" className={primaryLinkClassName}>
          Back to patients
        </Link>
      }
    >
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        {submitError && <Alert variant="error">{submitError}</Alert>}

        {duplicateQuery.data?.has_duplicates && (
          <DuplicatePatientAlert
            matches={duplicateMatches}
            acknowledged={acknowledgeDuplicate}
            onAcknowledgeChange={(checked) => {
              form.setValue("acknowledge_duplicate", checked, { shouldValidate: true });
              if (checked) {
                form.clearErrors("acknowledge_duplicate");
              }
            }}
            acknowledgeError={form.formState.errors.acknowledge_duplicate?.message}
          />
        )}

        <FormPageLayout
          sidebar={
            <FormHelpCard title="Registration tips">
              <p>MRN is assigned automatically after save.</p>
              <p>Phone must be a 10-digit Indian mobile number.</p>
              <p>Duplicate warnings are advisory — confirm before proceeding.</p>
              <p>Consent is required under DPDP for data processing.</p>
            </FormHelpCard>
          }
        >
          <FormSection title="Demographics" description="Core patient identity">
            <FormField name="first_name" control={form.control} label="First name" />
            <FormField name="last_name" control={form.control} label="Last name" />
            <FormField
              name="date_of_birth"
              control={form.control}
              label="Date of birth"
              type="date"
            />
            <FormField name="gender" control={form.control} label="Gender" as="select">
              <option value="female">Female</option>
              <option value="male">Male</option>
              <option value="other">Other</option>
            </FormField>
            <FormField name="blood_group" control={form.control} label="Blood group" as="select">
              <option value="">Not specified</option>
              {BLOOD_GROUPS.map((group) => (
                <option key={group} value={group}>
                  {group}
                </option>
              ))}
            </FormField>
            <FormField name="marital_status" control={form.control} label="Marital status" />
            <FormField name="occupation" control={form.control} label="Occupation" />
          </FormSection>

          <FormSection title="Contact" description="Primary phone and email">
            <FormField
              name="phone"
              control={form.control}
              label="Mobile phone"
              placeholder="10-digit number"
              description="Used for duplicate detection and patient communication."
            />
            <FormField name="email" control={form.control} label="Email" type="email" />
          </FormSection>

          <FormSection title="Address" description="Residential address (optional)">
            <FormField name="address_line1" control={form.control} label="Address line" />
            <FormField name="city" control={form.control} label="City" />
            <FormField name="state" control={form.control} label="State" />
            <FormField name="postal_code" control={form.control} label="Postal code" />
          </FormSection>

          <FormSection title="Identification" description="Optional ID proof details">
            <FormField name="id_proof_type" control={form.control} label="ID proof type" />
            <FormField name="id_proof_number" control={form.control} label="ID proof number" />
            {locations.length > 0 && (
              <FormField name="location_id" control={form.control} label="Branch" as="select">
                <option value="">Primary location</option>
                {locations.map((location) => (
                  <option key={location.id} value={location.id}>
                    {location.name}
                    {location.is_primary ? " (Primary)" : ""}
                  </option>
                ))}
              </FormField>
            )}
          </FormSection>

          <FormSection title="Consent" description="DPDP data-processing consent (required)" columns={1}>
            <FormField
              name="consent_method"
              control={form.control}
              label="Consent obtained via"
              as="select"
            >
              <option value="digital">Digital / registration form</option>
              <option value="written">Written form</option>
              <option value="verbal">Verbal (documented)</option>
            </FormField>

            <Controller
              name="data_processing_consent"
              control={form.control}
              render={({ field, fieldState }) => (
                <div className="space-y-1.5">
                  <label className="flex items-start gap-2 text-sm">
                    <input
                      type="checkbox"
                      className="mt-1"
                      checked={field.value}
                      onChange={(event) => field.onChange(event.target.checked)}
                    />
                    <span>
                      Patient (or authorized representative) consents to collection and processing
                      of personal and health data for hospital care and operations.
                    </span>
                  </label>
                  {fieldState.error?.message && (
                    <p className="text-xs text-error">{fieldState.error.message}</p>
                  )}
                </div>
              )}
            />
          </FormSection>

          <div className="flex flex-wrap gap-2 border-t border-border-light pt-6">
            <Button type="submit" disabled={saving}>
              {saving ? "Registering…" : "Register patient"}
            </Button>
            <Link to="/patients">
              <Button type="button" variant="secondary">
                Cancel
              </Button>
            </Link>
          </div>
        </FormPageLayout>
      </form>
    </AdminPageFrame>
  );
}
