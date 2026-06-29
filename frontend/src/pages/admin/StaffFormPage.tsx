import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { z } from "zod";
import { listDepartmentsRequest } from "@/api/endpoints/departments";
import { listLocationsRequest } from "@/api/endpoints/hospital";
import {
  createStaffRequest,
  deleteStaffRequest,
  getStaffRequest,
  updateStaffRequest,
} from "@/api/endpoints/staff";
import { ApiError } from "@/api/errors";
import type { Department } from "@/api/types/departments";
import type { HospitalLocation } from "@/api/types/hospital";
import type { StaffMember } from "@/api/types/staff";
import { FormField } from "@/components/forms/FormField";
import { AdminPageFrame, FormHelpCard, FormPageLayout, FormSection } from "@/components/enterprise";
import { Button, useToast } from "@/components/ui";
import { Alert } from "@/components/ui/Alert";

const staffSchema = z.object({
  employee_code: z.string().trim().min(1, "Employee code is required"),
  first_name: z.string().trim().min(1, "First name is required"),
  last_name: z.string().trim().min(1, "Last name is required"),
  email: z
    .string()
    .trim()
    .optional()
    .refine((value) => !value || z.string().email().safeParse(value).success, {
      message: "Enter a valid email",
    }),
  phone: z.string().optional(),
  department_id: z.string().optional(),
  designation: z.string().optional(),
  joining_date: z.string().min(1, "Joining date is required"),
  leaving_date: z.string().optional(),
  status: z.enum(["active", "on_leave", "terminated"]),
  location_id: z.string().optional(),
});

type StaffFormValues = z.infer<typeof staffSchema>;

function toCreatePayload(values: StaffFormValues) {
  return {
    employee_code: values.employee_code.trim().toUpperCase(),
    first_name: values.first_name.trim(),
    last_name: values.last_name.trim(),
    email: values.email?.trim() || undefined,
    phone: values.phone?.trim() || undefined,
    department_id: values.department_id || undefined,
    designation: values.designation?.trim() || undefined,
    joining_date: values.joining_date,
    leaving_date: values.leaving_date || undefined,
    status: values.status,
    location_id: values.location_id || undefined,
  };
}

function toUpdatePayload(values: StaffFormValues) {
  return {
    employee_code: values.employee_code.trim().toUpperCase(),
    first_name: values.first_name.trim(),
    last_name: values.last_name.trim(),
    email: values.email?.trim() || null,
    phone: values.phone?.trim() || null,
    department_id: values.department_id || null,
    designation: values.designation?.trim() || null,
    joining_date: values.joining_date,
    leaving_date: values.leaving_date || null,
    status: values.status,
    location_id: values.location_id || null,
  };
}

function staffToForm(staff: StaffMember): StaffFormValues {
  return {
    employee_code: staff.employee_code,
    first_name: staff.first_name,
    last_name: staff.last_name,
    email: staff.email ?? "",
    phone: staff.phone ?? "",
    department_id: staff.department_id ?? "",
    designation: staff.designation ?? "",
    joining_date: staff.joining_date,
    leaving_date: staff.leaving_date ?? "",
    status: staff.status,
    location_id: staff.location_id ?? "",
  };
}

const defaultValues: StaffFormValues = {
  employee_code: "",
  first_name: "",
  last_name: "",
  email: "",
  phone: "",
  department_id: "",
  designation: "",
  joining_date: new Date().toISOString().slice(0, 10),
  leaving_date: "",
  status: "active",
  location_id: "",
};

export function StaffFormPage() {
  const { staffId } = useParams<{ staffId: string }>();
  const isNew = staffId === undefined || staffId === "new";
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const toast = useToast();

  const staffQuery = useQuery({
    queryKey: ["admin", "staff", staffId],
    queryFn: () => getStaffRequest(staffId!),
    enabled: !isNew && Boolean(staffId),
  });

  const departmentsQuery = useQuery({
    queryKey: ["admin", "departments", "options"],
    queryFn: () => listDepartmentsRequest({ page: 1, page_size: 200, is_active: true }),
  });

  const locationsQuery = useQuery({
    queryKey: ["hospital", "locations"],
    queryFn: listLocationsRequest,
  });

  const form = useForm<StaffFormValues>({
    resolver: zodResolver(staffSchema),
    defaultValues,
  });

  useEffect(() => {
    if (staffQuery.data) {
      form.reset(staffToForm(staffQuery.data));
    }
  }, [staffQuery.data, form]);

  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ["admin", "staff"] });
    if (staffId) {
      await queryClient.invalidateQueries({ queryKey: ["admin", "staff", staffId] });
    }
  };

  const createMutation = useMutation({
    mutationFn: createStaffRequest,
    onSuccess: async (data) => {
      await invalidate();
      toast.success("Staff member created.");
      navigate(`/admin/staff/${data.id}`);
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : "Failed to create staff member.");
    },
  });

  const updateMutation = useMutation({
    mutationFn: (payload: ReturnType<typeof toUpdatePayload>) =>
      updateStaffRequest(staffId!, payload),
    onSuccess: async () => {
      await invalidate();
      toast.success("Staff member updated.");
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : "Failed to update staff member.");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteStaffRequest(staffId!),
    onSuccess: async () => {
      await invalidate();
      toast.success("Staff member terminated.");
      navigate("/admin/staff");
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : "Failed to terminate staff member.");
    },
  });

  function onSubmit(values: StaffFormValues) {
    if (isNew) {
      createMutation.mutate(toCreatePayload(values));
      return;
    }
    updateMutation.mutate(toUpdatePayload(values));
  }

  function handleTerminate() {
    const name = `${form.getValues("first_name")} ${form.getValues("last_name")}`.trim();
    if (!window.confirm(`Terminate ${name || "this staff member"}?`)) {
      return;
    }
    deleteMutation.mutate();
  }

  if (!isNew && staffQuery.isLoading) {
    return <p className="text-sm text-muted">Loading staff member…</p>;
  }

  if (!isNew && !staffQuery.isLoading && !staffQuery.data) {
    return (
      <AdminPageFrame title="Staff member not found" description="The requested employee record does not exist.">
        <Alert variant="error">Staff member not found.</Alert>
      </AdminPageFrame>
    );
  }

  const departments = departmentsQuery.data?.data ?? [];
  const locations = locationsQuery.data ?? [];
  const saving = createMutation.isPending || updateMutation.isPending;

  return (
    <AdminPageFrame
      title={isNew ? "Add staff member" : "Edit staff member"}
      description={
        !isNew && staffQuery.data?.is_doctor
          ? "This employee has a linked doctor profile."
          : "Capture employment details, department assignment, and lifecycle status."
      }
    >
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <FormPageLayout
          sidebar={
            <>
              <FormHelpCard title="Employment guidelines">
                <p>Employee codes must be unique across the hospital tenant.</p>
                <p>Terminated staff retain records for audit purposes.</p>
              </FormHelpCard>
              {!isNew && (
                <FormHelpCard title="Danger zone">
                  <p>Termination revokes active employment status.</p>
                  <Button
                    type="button"
                    variant="danger"
                    className="mt-3 w-full"
                    disabled={deleteMutation.isPending || staffQuery.data?.status === "terminated"}
                    onClick={handleTerminate}
                  >
                    {deleteMutation.isPending ? "Terminating…" : "Terminate employee"}
                  </Button>
                </FormHelpCard>
              )}
            </>
          }
        >
          <FormSection title="Identity" description="Basic employee identification">
            <FormField name="employee_code" control={form.control} label="Employee code" />
            <FormField name="designation" control={form.control} label="Designation" />
            <FormField name="first_name" control={form.control} label="First name" />
            <FormField name="last_name" control={form.control} label="Last name" />
          </FormSection>

          <FormSection title="Contact" description="Work communication details">
            <FormField name="email" control={form.control} label="Email" type="email" />
            <FormField name="phone" control={form.control} label="Phone" />
          </FormSection>

          <FormSection title="Organization" description="Department and branch assignment">
            <DepartmentField control={form.control} departments={departments} />
            <LocationField control={form.control} locations={locations} />
          </FormSection>

          <FormSection title="Employment" description="Dates and employment status">
            <FormField name="joining_date" control={form.control} label="Joining date" type="date" />
            <FormField name="leaving_date" control={form.control} label="Leaving date" type="date" />
            <StatusField control={form.control} />
          </FormSection>

          <div className="flex flex-wrap gap-2 border-t border-border-light pt-6">
            <Button type="submit" disabled={saving}>
              {saving ? "Saving…" : isNew ? "Create staff member" : "Save changes"}
            </Button>
          </div>
        </FormPageLayout>
      </form>
    </AdminPageFrame>
  );
}

function DepartmentField({
  control,
  departments,
}: {
  control: ReturnType<typeof useForm<StaffFormValues>>["control"];
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

function LocationField({
  control,
  locations,
}: {
  control: ReturnType<typeof useForm<StaffFormValues>>["control"];
  locations: HospitalLocation[];
}) {
  return (
    <FormField name="location_id" control={control} label="Branch" as="select">
      <option value="">No branch</option>
      {locations.map((location) => (
        <option key={location.id} value={location.id}>
          {location.name} ({location.code})
        </option>
      ))}
    </FormField>
  );
}

function StatusField({
  control,
}: {
  control: ReturnType<typeof useForm<StaffFormValues>>["control"];
}) {
  return (
    <FormField name="status" control={control} label="Status" as="select">
      <option value="active">Active</option>
      <option value="on_leave">On leave</option>
      <option value="terminated">Terminated</option>
    </FormField>
  );
}
