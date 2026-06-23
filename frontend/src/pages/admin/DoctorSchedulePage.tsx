import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { z } from "zod";
import {
  createDoctorScheduleRequest,
  deleteDoctorScheduleRequest,
  listDoctorSchedulesRequest,
  updateDoctorScheduleRequest,
} from "@/api/endpoints/doctor-schedules";
import { getDoctorRequest } from "@/api/endpoints/doctors";
import { listLocationsRequest } from "@/api/endpoints/hospital";
import { ApiError } from "@/api/errors";
import {
  DAY_LABELS,
  SLOT_DURATION_OPTIONS,
  type DoctorSchedule,
} from "@/api/types/doctor-schedules";
import type { HospitalLocation } from "@/api/types/hospital";
import { FormField } from "@/components/forms/FormField";
import {
  Button,
  Modal,
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

const scheduleSchema = z
  .object({
    day_of_week: z.string().min(1, "Day is required"),
    start_time: z.string().min(1, "Start time is required"),
    end_time: z.string().min(1, "End time is required"),
    slot_duration_minutes: z.string().min(1, "Slot duration is required"),
    max_patients_per_slot: z.string().min(1, "Max patients is required"),
    location_id: z.string().optional(),
    is_active: z.enum(["true", "false"]),
  })
  .refine((values) => values.end_time > values.start_time, {
    message: "End time must be after start time",
    path: ["end_time"],
  });

type ScheduleFormValues = z.infer<typeof scheduleSchema>;

function toPayload(values: ScheduleFormValues) {
  return {
    day_of_week: Number(values.day_of_week),
    start_time: values.start_time.length === 5 ? `${values.start_time}:00` : values.start_time,
    end_time: values.end_time.length === 5 ? `${values.end_time}:00` : values.end_time,
    slot_duration_minutes: Number(values.slot_duration_minutes),
    max_patients_per_slot: Number(values.max_patients_per_slot),
    location_id: values.location_id || undefined,
    is_active: values.is_active === "true",
  };
}

function scheduleToForm(schedule: DoctorSchedule): ScheduleFormValues {
  return {
    day_of_week: String(schedule.day_of_week),
    start_time: schedule.start_time.slice(0, 5),
    end_time: schedule.end_time.slice(0, 5),
    slot_duration_minutes: String(schedule.slot_duration_minutes),
    max_patients_per_slot: String(schedule.max_patients_per_slot),
    location_id: schedule.location_id ?? "",
    is_active: schedule.is_active ? "true" : "false",
  };
}

const defaultValues: ScheduleFormValues = {
  day_of_week: "1",
  start_time: "09:00",
  end_time: "13:00",
  slot_duration_minutes: "20",
  max_patients_per_slot: "1",
  location_id: "",
  is_active: "true",
};

function formatTime(value: string) {
  return value.slice(0, 5);
}

export function DoctorSchedulePage() {
  const { doctorId } = useParams<{ doctorId: string }>();
  const queryClient = useQueryClient();
  const toast = useToast();
  const [editing, setEditing] = useState<DoctorSchedule | null>(null);

  const doctorQuery = useQuery({
    queryKey: ["admin", "doctors", doctorId],
    queryFn: () => getDoctorRequest(doctorId!),
    enabled: Boolean(doctorId),
  });

  const schedulesQuery = useQuery({
    queryKey: ["admin", "doctors", doctorId, "schedules"],
    queryFn: () => listDoctorSchedulesRequest(doctorId!, { page: 1, page_size: 100 }),
    enabled: Boolean(doctorId),
  });

  const locationsQuery = useQuery({
    queryKey: ["hospital", "locations"],
    queryFn: listLocationsRequest,
  });

  const createForm = useForm<ScheduleFormValues>({
    resolver: zodResolver(scheduleSchema),
    defaultValues,
  });

  const editForm = useForm<ScheduleFormValues>({
    resolver: zodResolver(scheduleSchema),
    defaultValues,
  });

  useEffect(() => {
    if (editing) {
      editForm.reset(scheduleToForm(editing));
    }
  }, [editing, editForm]);

  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ["admin", "doctors", doctorId, "schedules"] });
  };

  const createMutation = useMutation({
    mutationFn: (payload: ReturnType<typeof toPayload>) =>
      createDoctorScheduleRequest(doctorId!, payload),
    onSuccess: async () => {
      await invalidate();
      createForm.reset(defaultValues);
      toast.success("Schedule slot added.");
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : "Failed to add schedule slot.");
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({
      scheduleId,
      payload,
    }: {
      scheduleId: string;
      payload: ReturnType<typeof toPayload>;
    }) => updateDoctorScheduleRequest(doctorId!, scheduleId, payload),
    onSuccess: async () => {
      await invalidate();
      setEditing(null);
      toast.success("Schedule slot updated.");
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : "Failed to update schedule slot.");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (scheduleId: string) => deleteDoctorScheduleRequest(doctorId!, scheduleId),
    onSuccess: async () => {
      await invalidate();
      setEditing(null);
      toast.success("Schedule slot removed.");
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : "Failed to remove schedule slot.");
    },
  });

  const locations = locationsQuery.data ?? [];
  const locationById = useMemo(
    () => new Map(locations.map((location) => [location.id, location])),
    [locations],
  );
  const schedules = schedulesQuery.data?.data ?? [];
  const doctor = doctorQuery.data;

  if (doctorQuery.isLoading) {
    return <p className="text-sm text-muted">Loading doctor…</p>;
  }

  if (!doctor) {
    return (
      <div className="space-y-4">
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-error">Doctor not found.</p>
        <Link to="/admin/doctors" className="text-sm text-primary hover:underline">
          Back to doctors
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <Link to={`/admin/doctors/${doctorId}`} className="text-sm text-primary hover:underline">
          ← Back to doctor profile
        </Link>
        <h2 className="mt-2 text-2xl font-semibold text-slate-900">Weekly schedule</h2>
        <p className="mt-1 text-sm text-muted">
          {doctor.first_name} {doctor.last_name} · {doctor.specialization}
        </p>
      </div>

      <form
        className="grid gap-4 rounded-lg border border-border bg-white p-6 sm:grid-cols-2"
        onSubmit={createForm.handleSubmit((values) => createMutation.mutate(toPayload(values)))}
      >
        <h3 className="sm:col-span-2 text-lg font-medium text-slate-900">Add schedule slot</h3>
        <DayField control={createForm.control} />
        <SlotDurationField control={createForm.control} />
        <FormField name="start_time" control={createForm.control} label="Start time" type="time" />
        <FormField name="end_time" control={createForm.control} label="End time" type="time" />
        <FormField
          name="max_patients_per_slot"
          control={createForm.control}
          label="Max patients per slot"
          type="number"
        />
        <LocationField control={createForm.control} locations={locations} />
        <ActiveField control={createForm.control} />
        <div className="sm:col-span-2">
          <Button type="submit" fullWidth disabled={createMutation.isPending}>
            {createMutation.isPending ? "Adding…" : "Add slot"}
          </Button>
        </div>
      </form>

      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableHeaderCell>Day</TableHeaderCell>
              <TableHeaderCell>Time</TableHeaderCell>
              <TableHeaderCell>Slot</TableHeaderCell>
              <TableHeaderCell>Branch</TableHeaderCell>
              <TableHeaderCell>Status</TableHeaderCell>
              <TableHeaderCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {schedulesQuery.isLoading && (
              <TableLoading colSpan={6}>Loading schedule…</TableLoading>
            )}
            {schedules.map((schedule) => (
              <TableRow key={schedule.id}>
                <TableCell>{DAY_LABELS[schedule.day_of_week]}</TableCell>
                <TableCell>
                  {formatTime(schedule.start_time)} – {formatTime(schedule.end_time)}
                </TableCell>
                <TableCell>
                  {schedule.slot_duration_minutes} min · max {schedule.max_patients_per_slot}
                </TableCell>
                <TableCell>
                  {schedule.location_id
                    ? (locationById.get(schedule.location_id)?.name ?? "—")
                    : "—"}
                </TableCell>
                <TableCell className="capitalize">
                  {schedule.is_active ? "active" : "inactive"}
                </TableCell>
                <TableCell className="text-right">
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => setEditing(schedule)}
                  >
                    Edit
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {!schedulesQuery.isLoading && schedules.length === 0 && (
              <TableEmpty colSpan={6}>No schedule slots configured.</TableEmpty>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Modal
        open={Boolean(editing)}
        title="Edit schedule slot"
        onClose={() => setEditing(null)}
        footer={
          <div className="flex flex-wrap items-center justify-between gap-2">
            <Button
              type="button"
              variant="secondary"
              className="text-error"
              disabled={deleteMutation.isPending}
              onClick={() => {
                if (!editing) return;
                if (!window.confirm("Remove this schedule slot?")) return;
                deleteMutation.mutate(editing.id);
              }}
            >
              {deleteMutation.isPending ? "Removing…" : "Remove"}
            </Button>
            <div className="flex gap-2">
              <Button type="button" variant="secondary" onClick={() => setEditing(null)}>
                Cancel
              </Button>
              <Button
                type="submit"
                form="edit-schedule-form"
                disabled={updateMutation.isPending}
              >
                {updateMutation.isPending ? "Saving…" : "Save changes"}
              </Button>
            </div>
          </div>
        }
      >
        <form
          id="edit-schedule-form"
          className="grid gap-4 sm:grid-cols-2"
          onSubmit={editForm.handleSubmit((values) => {
            if (!editing) return;
            updateMutation.mutate({ scheduleId: editing.id, payload: toPayload(values) });
          })}
        >
          <DayField control={editForm.control} />
          <SlotDurationField control={editForm.control} />
          <FormField name="start_time" control={editForm.control} label="Start time" type="time" />
          <FormField name="end_time" control={editForm.control} label="End time" type="time" />
          <FormField
            name="max_patients_per_slot"
            control={editForm.control}
            label="Max patients per slot"
            type="number"
          />
          <LocationField control={editForm.control} locations={locations} />
          <ActiveField control={editForm.control} />
        </form>
      </Modal>
    </div>
  );
}

function DayField({
  control,
}: {
  control: ReturnType<typeof useForm<ScheduleFormValues>>["control"];
}) {
  return (
    <FormField name="day_of_week" control={control} label="Day" as="select">
      {DAY_LABELS.map((label, index) => (
        <option key={label} value={String(index)}>
          {label}
        </option>
      ))}
    </FormField>
  );
}

function SlotDurationField({
  control,
}: {
  control: ReturnType<typeof useForm<ScheduleFormValues>>["control"];
}) {
  return (
    <FormField name="slot_duration_minutes" control={control} label="Slot duration" as="select">
      {SLOT_DURATION_OPTIONS.map((minutes) => (
        <option key={minutes} value={String(minutes)}>
          {minutes} minutes
        </option>
      ))}
    </FormField>
  );
}

function LocationField({
  control,
  locations,
}: {
  control: ReturnType<typeof useForm<ScheduleFormValues>>["control"];
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

function ActiveField({
  control,
}: {
  control: ReturnType<typeof useForm<ScheduleFormValues>>["control"];
}) {
  return (
    <FormField name="is_active" control={control} label="Status" as="select">
      <option value="true">Active</option>
      <option value="false">Inactive</option>
    </FormField>
  );
}
