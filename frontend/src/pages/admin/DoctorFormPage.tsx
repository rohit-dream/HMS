import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useMemo } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { z } from "zod";
import { listDepartmentsRequest } from "@/api/endpoints/departments";
import {
  createDoctorRequest,
  deleteDoctorRequest,
  getDoctorRequest,
  updateDoctorRequest,
} from "@/api/endpoints/doctors";
import { listStaffRequest } from "@/api/endpoints/staff";
import { ApiError } from "@/api/errors";
import type { Department } from "@/api/types/departments";
import type { Doctor } from "@/api/types/doctors";
import type { StaffMember } from "@/api/types/staff";
import { FormField } from "@/components/forms/FormField";
import { Button, useToast } from "@/components/ui";

const doctorBaseSchema = z.object({
  staff_id: z.string().optional(),
  specialization: z.string().trim().min(1, "Specialization is required"),
  registration_number: z.string().optional(),
  qualification: z.string().optional(),
  consultation_fee: z
    .string()
    .trim()
    .min(1, "Consultation fee is required")
    .refine((value) => !Number.isNaN(Number(value)) && Number(value) >= 0, {
      message: "Fee must be zero or greater",
    }),
  follow_up_fee: z
    .string()
    .optional()
    .refine((value) => !value || (!Number.isNaN(Number(value)) && Number(value) >= 0), {
      message: "Fee must be zero or greater",
    }),
  department_id: z.string().optional(),
  bio: z.string().optional(),
  is_available: z.enum(["true", "false"]),
});

const createDoctorSchema = doctorBaseSchema.extend({
  staff_id: z.string().min(1, "Staff member is required"),
});

type DoctorFormValues = z.infer<typeof doctorBaseSchema>;

function toCreatePayload(values: DoctorFormValues) {
  return {
    staff_id: values.staff_id!,
    specialization: values.specialization.trim(),
    registration_number: values.registration_number?.trim() || undefined,
    qualification: values.qualification?.trim() || undefined,
    consultation_fee: Number(values.consultation_fee).toFixed(2),
    follow_up_fee: values.follow_up_fee ? Number(values.follow_up_fee).toFixed(2) : undefined,
    department_id: values.department_id || undefined,
    bio: values.bio?.trim() || undefined,
    is_available: values.is_available === "true",
  };
}

function toUpdatePayload(values: DoctorFormValues) {
  return {
    specialization: values.specialization.trim(),
    registration_number: values.registration_number?.trim() || null,
    qualification: values.qualification?.trim() || null,
    consultation_fee: Number(values.consultation_fee).toFixed(2),
    follow_up_fee: values.follow_up_fee ? Number(values.follow_up_fee).toFixed(2) : null,
    department_id: values.department_id || null,
    bio: values.bio?.trim() || null,
    is_available: values.is_available === "true",
  };
}

function doctorToForm(doctor: Doctor): DoctorFormValues {
  return {
    staff_id: doctor.staff_id,
    specialization: doctor.specialization,
    registration_number: doctor.registration_number ?? "",
    qualification: doctor.qualification ?? "",
    consultation_fee: doctor.consultation_fee,
    follow_up_fee: doctor.follow_up_fee ?? "",
    department_id: doctor.department_id ?? "",
    bio: doctor.bio ?? "",
    is_available: doctor.is_available ? "true" : "false",
  };
}

const defaultValues: DoctorFormValues = {
  staff_id: "",
  specialization: "",
  registration_number: "",
  qualification: "",
  consultation_fee: "",
  follow_up_fee: "",
  department_id: "",
  bio: "",
  is_available: "true",
};

export function DoctorFormPage() {
  const { doctorId } = useParams<{ doctorId: string }>();
  const isNew = !doctorId || doctorId === "new";
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const toast = useToast();

  const doctorQuery = useQuery({
    queryKey: ["admin", "doctors", doctorId],
    queryFn: () => getDoctorRequest(doctorId!),
    enabled: !isNew,
  });

  const staffQuery = useQuery({
    queryKey: ["admin", "staff", "doctor-candidates"],
    queryFn: () => listStaffRequest({ status: "active", page: 1, page_size: 200 }),
    enabled: isNew,
  });

  const departmentsQuery = useQuery({
    queryKey: ["admin", "departments", "options"],
    queryFn: () => listDepartmentsRequest({ page: 1, page_size: 200, is_active: true }),
  });

  const form = useForm<DoctorFormValues>({
    resolver: zodResolver(isNew ? createDoctorSchema : doctorBaseSchema),
    defaultValues,
  });

  useEffect(() => {
    if (doctorQuery.data) {
      form.reset(doctorToForm(doctorQuery.data));
    }
  }, [doctorQuery.data, form]);

  const eligibleStaff = useMemo(
    () => (staffQuery.data?.data ?? []).filter((member) => !member.is_doctor),
    [staffQuery.data],
  );

  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ["admin", "doctors"] });
    await queryClient.invalidateQueries({ queryKey: ["admin", "staff"] });
    if (doctorId) {
      await queryClient.invalidateQueries({ queryKey: ["admin", "doctors", doctorId] });
    }
  };

  const createMutation = useMutation({
    mutationFn: createDoctorRequest,
    onSuccess: async (data) => {
      await invalidate();
      toast.success("Doctor profile created.");
      navigate(`/admin/doctors/${data.id}`);
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : "Failed to create doctor.");
    },
  });

  const updateMutation = useMutation({
    mutationFn: (payload: ReturnType<typeof toUpdatePayload>) =>
      updateDoctorRequest(doctorId!, payload),
    onSuccess: async () => {
      await invalidate();
      toast.success("Doctor profile updated.");
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : "Failed to update doctor.");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteDoctorRequest(doctorId!),
    onSuccess: async () => {
      await invalidate();
      toast.success("Doctor profile removed.");
      navigate("/admin/doctors");
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : "Failed to remove doctor.");
    },
  });

  function onSubmit(values: DoctorFormValues) {
    if (isNew) {
      createMutation.mutate(toCreatePayload(values));
      return;
    }
    updateMutation.mutate(toUpdatePayload(values));
  }

  function handleDelete() {
    const name = doctorQuery.data
      ? `${doctorQuery.data.first_name} ${doctorQuery.data.last_name}`
      : "this doctor";
    if (!window.confirm(`Remove doctor profile for ${name}?`)) {
      return;
    }
    deleteMutation.mutate();
  }

  if (!isNew && doctorQuery.isLoading) {
    return <p className="text-sm text-muted">Loading doctor…</p>;
  }

  if (!isNew && !doctorQuery.isLoading && !doctorQuery.data) {
    return (
      <div className="space-y-4">
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-error">Doctor not found.</p>
        <Link to="/admin/doctors" className="text-sm text-primary hover:underline">
          Back to doctors
        </Link>
      </div>
    );
  }

  const departments = departmentsQuery.data?.data ?? [];
  const saving = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <Link to="/admin/doctors" className="text-sm text-primary hover:underline">
          ← Back to doctors
        </Link>
        <h2 className="mt-2 text-2xl font-semibold text-slate-900">
          {isNew ? "Add doctor" : "Edit doctor"}
        </h2>
        {!isNew && doctorQuery.data && (
          <p className="mt-1 text-sm text-muted">
            {doctorQuery.data.first_name} {doctorQuery.data.last_name} ·{" "}
            {doctorQuery.data.employee_code}
          </p>
        )}
      </div>

      <form
        className="grid gap-4 rounded-lg border border-border bg-white p-6 sm:grid-cols-2"
        onSubmit={form.handleSubmit(onSubmit)}
      >
        {isNew ? (
          <StaffField control={form.control} staff={eligibleStaff} />
        ) : null}
        <FormField name="specialization" control={form.control} label="Specialization" />
        <FormField name="registration_number" control={form.control} label="Registration no." />
        <FormField name="qualification" control={form.control} label="Qualification" />
        <FormField
          name="consultation_fee"
          control={form.control}
          label="Consultation fee"
          type="number"
        />
        <FormField name="follow_up_fee" control={form.control} label="Follow-up fee" type="number" />
        <DepartmentField control={form.control} departments={departments} />
        <AvailabilityField control={form.control} />
        <FormField
          name="bio"
          control={form.control}
          label="Bio"
          as="textarea"
          className="sm:col-span-2"
        />

        <div className="flex flex-wrap gap-2 sm:col-span-2">
          <Button type="submit" disabled={saving}>
            {saving ? "Saving…" : isNew ? "Create doctor" : "Save changes"}
          </Button>
          {!isNew && (
            <>
              <Link
                to={`/admin/doctors/${doctorId}/schedule`}
                className="inline-flex items-center justify-center rounded-lg border border-border bg-white px-4 py-2 text-sm font-medium text-slate-900 hover:bg-surface"
              >
                Manage schedule
              </Link>
              <Button
                type="button"
                variant="danger"
                disabled={deleteMutation.isPending}
                onClick={handleDelete}
              >
                {deleteMutation.isPending ? "Removing…" : "Remove doctor"}
              </Button>
            </>
          )}
        </div>
      </form>
    </div>
  );
}

function StaffField({
  control,
  staff,
}: {
  control: ReturnType<typeof useForm<DoctorFormValues>>["control"];
  staff: StaffMember[];
}) {
  return (
    <FormField
      name="staff_id"
      control={control}
      label="Staff member"
      as="select"
      className="sm:col-span-2"
      description="Only active staff without an existing doctor profile are listed."
    >
      <option value="">Select staff member</option>
      {staff.map((member) => (
        <option key={member.id} value={member.id}>
          {member.first_name} {member.last_name} ({member.employee_code})
        </option>
      ))}
    </FormField>
  );
}

function DepartmentField({
  control,
  departments,
}: {
  control: ReturnType<typeof useForm<DoctorFormValues>>["control"];
  departments: Department[];
}) {
  return (
    <FormField name="department_id" control={control} label="Department" as="select">
      <option value="">No department</option>
      {departments.map((department) => (
        <option key={department.id} value={department.id}>
          {department.name} ({department.code})
        </option>
      ))}
    </FormField>
  );
}

function AvailabilityField({
  control,
}: {
  control: ReturnType<typeof useForm<DoctorFormValues>>["control"];
}) {
  return (
    <FormField name="is_available" control={control} label="Accepting patients" as="select">
      <option value="true">Yes</option>
      <option value="false">No</option>
    </FormField>
  );
}
