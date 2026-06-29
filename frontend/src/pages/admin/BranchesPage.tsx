import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { z } from "zod";
import {
  createLocationRequest,
  listLocationsRequest,
  updateLocationRequest,
} from "@/api/endpoints/hospital";
import { ApiError } from "@/api/errors";
import type { HospitalLocation } from "@/api/types/hospital";
import { FormField } from "@/components/forms/FormField";
import {
  Button,
  Input,
  PageHeader,
  PageShell,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableEmpty,
  TableHead,
  TableHeaderCell,
  TableLoading,
  TableRow,
  useToast,
} from "@/components/ui";

const createBranchSchema = z.object({
  name: z.string().trim().min(1, "Name is required"),
  code: z.string().trim().min(1, "Code is required"),
  city: z.string().optional(),
  phone: z.string().optional(),
});

type CreateBranchForm = z.infer<typeof createBranchSchema>;

export function BranchesPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const locationsQuery = useQuery({
    queryKey: ["hospital", "locations"],
    queryFn: listLocationsRequest,
  });

  const form = useForm<CreateBranchForm>({
    resolver: zodResolver(createBranchSchema),
    defaultValues: { name: "", code: "", city: "", phone: "" },
  });

  const createMutation = useMutation({
    mutationFn: createLocationRequest,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["hospital", "locations"] });
      form.reset();
      toast.success("Branch created.");
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : "Failed to create branch.");
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, phone: branchPhone }: { id: string; phone: string }) =>
      updateLocationRequest(id, { phone: branchPhone || undefined }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["hospital", "locations"] });
      toast.success("Branch updated.");
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : "Failed to update branch.");
    },
  });

  function onCreate(values: CreateBranchForm) {
    createMutation.mutate({
      name: values.name.trim(),
      code: values.code.trim().toUpperCase(),
      city: values.city?.trim() || undefined,
      phone: values.phone?.trim() || undefined,
    });
  }

  const locations = locationsQuery.data ?? [];

  return (
    <PageShell>
      <PageHeader
        title="Branches"
        description="Manage hospital locations and branch codes."
      />

      <form
        className="form-card grid gap-4 sm:grid-cols-2"
        onSubmit={form.handleSubmit(onCreate)}
      >
        <h3 className="section-title sm:col-span-2">Add branch</h3>
        <FormField name="name" control={form.control} label="Name" />
        <FormField name="code" control={form.control} label="Code" />
        <FormField name="city" control={form.control} label="City" />
        <FormField name="phone" control={form.control} label="Phone" />
        <div className="sm:col-span-2">
          <Button type="submit" fullWidth disabled={createMutation.isPending}>
            {createMutation.isPending ? "Creating…" : "Create branch"}
          </Button>
        </div>
      </form>

      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableHeaderCell>Name</TableHeaderCell>
              <TableHeaderCell>Code</TableHeaderCell>
              <TableHeaderCell>City</TableHeaderCell>
              <TableHeaderCell>Phone</TableHeaderCell>
              <TableHeaderCell>Status</TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {locationsQuery.isLoading && <TableLoading colSpan={5}>Loading branches…</TableLoading>}
            {locations.map((location) => (
              <BranchRow
                key={location.id}
                location={location}
                onSavePhone={(branchPhone) =>
                  updateMutation.mutate({ id: location.id, phone: branchPhone })
                }
                saving={updateMutation.isPending}
              />
            ))}
            {!locationsQuery.isLoading && locations.length === 0 && (
              <TableEmpty colSpan={5}>No branches yet.</TableEmpty>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </PageShell>
  );
}

function BranchRow({
  location,
  onSavePhone,
  saving,
}: {
  location: HospitalLocation;
  onSavePhone: (phone: string) => void;
  saving: boolean;
}) {
  const [phone, setPhone] = useState(location.phone ?? "");

  return (
    <TableRow>
      <TableCell>
        {location.name}
        {location.is_primary && (
          <span className="ml-2 rounded-full border border-blue-200 bg-blue-50 px-2 py-0.5 text-xs text-primary">Primary</span>
        )}
      </TableCell>
      <TableCell className="font-mono text-xs">{location.code}</TableCell>
      <TableCell>{location.city ?? "—"}</TableCell>
      <TableCell>
        <div className="flex gap-2">
          <Input
            className="min-w-[8rem] px-2 py-1"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
          <Button
            type="button"
            variant="secondary"
            size="sm"
            disabled={saving || phone === (location.phone ?? "")}
            onClick={() => onSavePhone(phone)}
          >
            Save
          </Button>
        </div>
      </TableCell>
      <TableCell className="capitalize">{location.is_active ? "active" : "inactive"}</TableCell>
    </TableRow>
  );
}
