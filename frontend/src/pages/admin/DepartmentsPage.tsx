import { zodResolver } from "@hookform/resolvers/zod";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { z } from "zod";
import {
  createDepartmentRequest,
  deleteDepartmentRequest,
  listDepartmentsRequest,
  updateDepartmentRequest,
} from "@/api/endpoints/departments";
import { listLocationsRequest } from "@/api/endpoints/hospital";
import { ApiError } from "@/api/errors";
import type { Department } from "@/api/types/departments";
import type { HospitalLocation } from "@/api/types/hospital";
import { FormField } from "@/components/forms/FormField";
import {
  AdminPageFrame,
  DataGridShell,
  DataToolbar,
  FormSection,
} from "@/components/enterprise";
import { GlassCard } from "@/components/ui/GlassCard";
import { Badge } from "@/components/ui/Badge";
import {
  Button,
  Modal,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableLoading,
  TableRow,
  useToast,
} from "@/components/ui";

const deptCodePattern = /^[A-Z0-9]{2,20}$/;

const departmentSchema = z.object({
  name: z.string().trim().min(2, "Name must be at least 2 characters"),
  code: z
    .string()
    .trim()
    .transform((value) => value.toUpperCase())
    .refine((value) => deptCodePattern.test(value), {
      message: "Code must be 2–20 uppercase letters or numbers",
    }),
  location_id: z.string().optional(),
  is_active: z.enum(["true", "false"]),
});

type DepartmentForm = z.infer<typeof departmentSchema>;

function toPayload(values: DepartmentForm) {
  return {
    name: values.name.trim(),
    code: values.code,
    location_id: values.location_id || undefined,
    is_active: values.is_active === "true",
  };
}

function departmentToForm(department: Department): DepartmentForm {
  return {
    name: department.name,
    code: department.code,
    location_id: department.location_id ?? "",
    is_active: department.is_active ? "true" : "false",
  };
}

export function DepartmentsPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [editing, setEditing] = useState<Department | null>(null);

  const locationsQuery = useQuery({
    queryKey: ["hospital", "locations"],
    queryFn: listLocationsRequest,
  });

  const departmentsQuery = useQuery({
    queryKey: ["admin", "departments", query],
    queryFn: () => listDepartmentsRequest({ q: query || undefined, page: 1, page_size: 100 }),
  });

  const createForm = useForm<DepartmentForm>({
    resolver: zodResolver(departmentSchema),
    defaultValues: { name: "", code: "", location_id: "", is_active: "true" },
  });

  const editForm = useForm<DepartmentForm>({
    resolver: zodResolver(departmentSchema),
    defaultValues: { name: "", code: "", location_id: "", is_active: "true" },
  });

  useEffect(() => {
    if (editing) {
      editForm.reset(departmentToForm(editing));
    }
  }, [editing, editForm]);

  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ["admin", "departments"] });
  };

  const createMutation = useMutation({
    mutationFn: createDepartmentRequest,
    onSuccess: async () => {
      await invalidate();
      createForm.reset({ name: "", code: "", location_id: "", is_active: "true" });
      toast.success("Department created.");
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : "Failed to create department.");
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: ReturnType<typeof toPayload> }) =>
      updateDepartmentRequest(id, payload),
    onSuccess: async () => {
      await invalidate();
      setEditing(null);
      toast.success("Department updated.");
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : "Failed to update department.");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteDepartmentRequest,
    onSuccess: async () => {
      await invalidate();
      setEditing(null);
      toast.success("Department deleted.");
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : "Failed to delete department.");
    },
  });

  function handleSearch(event: FormEvent) {
    event.preventDefault();
    setQuery(search.trim());
  }

  function onCreate(values: DepartmentForm) {
    createMutation.mutate(toPayload(values));
  }

  function onUpdate(values: DepartmentForm) {
    if (!editing) return;
    updateMutation.mutate({ id: editing.id, payload: toPayload(values) });
  }

  function handleDelete() {
    if (!editing) return;
    if (!window.confirm(`Delete department "${editing.name}"? This cannot be undone.`)) {
      return;
    }
    deleteMutation.mutate(editing.id);
  }

  const locations = locationsQuery.data ?? [];
  const locationById = useMemo(
    () => new Map(locations.map((location) => [location.id, location])),
    [locations],
  );
  const departments = departmentsQuery.data?.data ?? [];

  return (
    <AdminPageFrame
      title="Department structure"
      description="Define clinical and administrative units mapped to hospital branches."
    >
      <div className="grid gap-6 xl:grid-cols-12">
        <div className="space-y-4 xl:col-span-8">
          <DataToolbar
            searchValue={search}
            onSearchChange={setSearch}
            onSearchSubmit={handleSearch}
            searchPlaceholder="Search by name or code"
          />

          <DataGridShell>
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeaderCell>Department</TableHeaderCell>
                  <TableHeaderCell>Code</TableHeaderCell>
                  <TableHeaderCell>Branch</TableHeaderCell>
                  <TableHeaderCell>Status</TableHeaderCell>
                  <TableHeaderCell className="text-right">Actions</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {departmentsQuery.isLoading && (
                  <TableLoading colSpan={5}>Loading departments…</TableLoading>
                )}
                {departments.map((department) => (
                  <TableRow key={department.id}>
                    <TableCell className="font-medium">{department.name}</TableCell>
                    <TableCell className="font-mono text-xs">{department.code}</TableCell>
                    <TableCell>
                      {department.location_id
                        ? (locationById.get(department.location_id)?.name ?? "—")
                        : "—"}
                    </TableCell>
                    <TableCell>
                      <Badge variant={department.is_active ? "success" : "neutral"}>
                        {department.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => setEditing(department)}
                      >
                        Edit
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
                {!departmentsQuery.isLoading && departments.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="py-12 text-center text-muted">
                      No departments found. Create your first department using the panel on the right.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </DataGridShell>
        </div>

        <GlassCard strong className="h-fit xl:col-span-4">
          <form className="space-y-6" onSubmit={createForm.handleSubmit(onCreate)}>
            <FormSection title="New department" description="Departments organize staff, doctors, and reporting.">
              <FormField name="name" control={createForm.control} label="Department name" className="md:col-span-2" />
              <FormField
                name="code"
                control={createForm.control}
                label="Short code"
                description="2–20 uppercase letters or numbers"
                className="md:col-span-2"
              />
              <LocationField control={createForm.control} locations={locations} />
              <StatusField control={createForm.control} />
            </FormSection>
            <Button type="submit" fullWidth disabled={createMutation.isPending}>
              {createMutation.isPending ? "Creating…" : "Create department"}
            </Button>
          </form>
        </GlassCard>
      </div>

      <Modal
        open={Boolean(editing)}
        title="Edit department"
        onClose={() => setEditing(null)}
        footer={
          <div className="flex flex-wrap items-center justify-between gap-2">
            <Button
              type="button"
              variant="secondary"
              className="text-error"
              disabled={deleteMutation.isPending}
              onClick={handleDelete}
            >
              {deleteMutation.isPending ? "Deleting…" : "Delete"}
            </Button>
            <div className="flex gap-2">
              <Button type="button" variant="secondary" onClick={() => setEditing(null)}>
                Cancel
              </Button>
              <Button
                type="submit"
                form="edit-department-form"
                disabled={updateMutation.isPending}
              >
                {updateMutation.isPending ? "Saving…" : "Save changes"}
              </Button>
            </div>
          </div>
        }
      >
        <form
          id="edit-department-form"
          className="grid gap-4 sm:grid-cols-2"
          onSubmit={editForm.handleSubmit(onUpdate)}
        >
          <FormField name="name" control={editForm.control} label="Name" />
          <FormField name="code" control={editForm.control} label="Code" />
          <LocationField control={editForm.control} locations={locations} />
          <StatusField control={editForm.control} />
        </form>
      </Modal>
    </AdminPageFrame>
  );
}

function LocationField({
  control,
  locations,
}: {
  control: ReturnType<typeof useForm<DepartmentForm>>["control"];
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
  control: ReturnType<typeof useForm<DepartmentForm>>["control"];
}) {
  return (
    <FormField name="is_active" control={control} label="Status" as="select">
      <option value="true">Active</option>
      <option value="false">Inactive</option>
    </FormField>
  );
}
