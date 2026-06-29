import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowDown, ArrowUp, CheckCircle2, PhoneCall, SkipForward, Stethoscope } from "lucide-react";
import type { OpdQueueEntry, OpdQueuePoll } from "@/api/types/opd";
import {
  Alert,
  Button,
  FieldLabel,
  Input,
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
import { GlassCard } from "@/components/ui/GlassCard";
import { OpdQueuePriorityBadge } from "@/features/opd/components/OpdQueuePriorityBadge";
import { OpdQueueStatusBadge } from "@/features/opd/components/OpdQueueStatusBadge";
import { useOpdQueueActions } from "@/features/opd/hooks/useOpdQueueActions";
import { cn } from "@/lib/cn";

interface OpdQueueBoardProps {
  board: OpdQueuePoll | null;
  isLoading: boolean;
  canManageQueue: boolean;
  canConsult: boolean;
  onQueueChanged: () => void;
}

function waitingEntries(entries: OpdQueueEntry[]): OpdQueueEntry[] {
  return entries
    .filter((entry) => entry.status === "waiting")
    .sort((left, right) => left.token_number - right.token_number);
}

function reorderPosition(
  entries: OpdQueueEntry[],
  entryId: string,
  direction: "up" | "down",
): number | null {
  const ordered = waitingEntries(entries);
  const index = ordered.findIndex((entry) => entry.id === entryId);
  if (index < 0) return null;

  if (direction === "up") {
    if (index === 0) return null;
    return index;
  }

  if (index >= ordered.length - 1) return null;
  return index + 2;
}

function formatCalledAt(value: string | null): string {
  if (!value) return "—";
  return new Date(value).toLocaleTimeString(undefined, {
    hour: "numeric",
    minute: "2-digit",
  });
}

export function OpdQueueBoard({
  board,
  isLoading,
  canManageQueue,
  canConsult,
  onQueueChanged,
}: OpdQueueBoardProps) {
  const toast = useToast();
  const { callMutation, skipMutation, completeMutation, reorderMutation, isPending } =
    useOpdQueueActions(onQueueChanged);

  const [skipEntry, setSkipEntry] = useState<OpdQueueEntry | null>(null);
  const [skipReason, setSkipReason] = useState("");
  const [skipError, setSkipError] = useState<string | null>(null);

  const entries = board?.entries ?? [];
  const activeEntries = useMemo(
    () =>
      entries.filter((entry) => entry.status !== "completed" && entry.status !== "skipped"),
    [entries],
  );

  async function handleCall(queueId: string) {
    try {
      await callMutation.mutateAsync(queueId);
      toast.success("Patient called");
    } catch {
      toast.error("Unable to call patient");
    }
  }

  async function handleComplete(queueId: string) {
    try {
      await completeMutation.mutateAsync(queueId);
      toast.success("Queue entry completed");
    } catch {
      toast.error("Unable to complete queue entry");
    }
  }

  async function handleReorder(entryId: string, direction: "up" | "down") {
    if (!board) return;
    const position = reorderPosition(board.entries, entryId, direction);
    if (position === null) return;

    try {
      await reorderMutation.mutateAsync({
        queueId: entryId,
        payload: { position },
      });
      toast.success("Queue order updated");
    } catch {
      toast.error("Unable to reorder queue");
    }
  }

  async function submitSkip(event: React.FormEvent) {
    event.preventDefault();
    if (!skipEntry) return;

    const reason = skipReason.trim();
    if (reason.length < 1) {
      setSkipError("A skip reason is required.");
      return;
    }

    try {
      await skipMutation.mutateAsync({
        queueId: skipEntry.id,
        payload: { reason },
      });
      toast.success("Patient skipped");
      setSkipEntry(null);
      setSkipReason("");
      setSkipError(null);
    } catch {
      toast.error("Unable to skip patient");
    }
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <GlassCard padding="md">
          <p className="text-xs font-medium uppercase tracking-wide text-muted">Current token</p>
          <p className="mt-2 text-3xl font-semibold text-foreground">
            {board?.current_token ?? "—"}
          </p>
        </GlassCard>
        <GlassCard padding="md">
          <p className="text-xs font-medium uppercase tracking-wide text-muted">Waiting</p>
          <p className="mt-2 text-3xl font-semibold text-foreground">{board?.waiting_count ?? 0}</p>
        </GlassCard>
        <GlassCard padding="md" className="sm:col-span-2 xl:col-span-1">
          <p className="text-xs font-medium uppercase tracking-wide text-muted">Live updates</p>
          <p className="mt-2 text-sm text-foreground">
            {canManageQueue
              ? `Polling every ${board?.poll_interval_seconds ?? 5}s`
              : "View only — queue actions require manage permission"}
          </p>
        </GlassCard>
      </div>

      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableHeaderCell>Token</TableHeaderCell>
              <TableHeaderCell>Patient</TableHeaderCell>
              <TableHeaderCell>Complaint</TableHeaderCell>
              <TableHeaderCell>Priority</TableHeaderCell>
              <TableHeaderCell>Status</TableHeaderCell>
              <TableHeaderCell>Called at</TableHeaderCell>
              {(canManageQueue || canConsult) && (
                <TableHeaderCell className="text-right">Actions</TableHeaderCell>
              )}
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading && entries.length === 0 ? (
              <TableLoading colSpan={canManageQueue || canConsult ? 7 : 6} />
            ) : activeEntries.length === 0 ? (
              <TableEmpty colSpan={canManageQueue || canConsult ? 7 : 6}>
                No patients in the queue for this doctor today.
              </TableEmpty>
            ) : (
              activeEntries.map((entry) => {
                const isWaiting = entry.status === "waiting";
                const isActive =
                  entry.status === "called" || entry.status === "in_consultation";
                const waitingIndex = waitingEntries(board?.entries ?? []).findIndex(
                  (item) => item.id === entry.id,
                );
                const canMoveUp = isWaiting && waitingIndex > 0;
                const canMoveDown =
                  isWaiting &&
                  waitingIndex >= 0 &&
                  waitingIndex < waitingEntries(board?.entries ?? []).length - 1;

                return (
                  <TableRow
                    key={entry.id}
                    className={cn(
                      entry.token_number === board?.current_token &&
                        "bg-primary/5 hover:bg-primary/10",
                    )}
                  >
                    <TableCell className="font-semibold">#{entry.token_number}</TableCell>
                    <TableCell>{entry.patient_name ?? "Unknown patient"}</TableCell>
                    <TableCell className="max-w-xs truncate">
                      {entry.chief_complaint ?? "—"}
                    </TableCell>
                    <TableCell>
                      <OpdQueuePriorityBadge priority={entry.priority} />
                    </TableCell>
                    <TableCell>
                      <OpdQueueStatusBadge status={entry.status} />
                    </TableCell>
                    <TableCell>{formatCalledAt(entry.called_at)}</TableCell>
                    {(canManageQueue || canConsult) && (
                      <TableCell>
                        <div className="flex flex-wrap justify-end gap-2">
                          {canConsult && (
                            <Link
                              to={`/opd/consult/${entry.opd_visit_id}`}
                              className="inline-flex items-center justify-center rounded-lg border border-border bg-card px-3 py-1.5 text-xs font-medium text-foreground transition-all duration-200 hover:bg-hover"
                            >
                              <Stethoscope className="mr-1 h-4 w-4" />
                              Consult
                            </Link>
                          )}
                          {canManageQueue && isWaiting && (
                            <>
                              <Button
                                size="sm"
                                variant="outline"
                                disabled={!canMoveUp || isPending}
                                onClick={() => handleReorder(entry.id, "up")}
                                aria-label={`Move token ${entry.token_number} up`}
                              >
                                <ArrowUp className="h-4 w-4" />
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                disabled={!canMoveDown || isPending}
                                onClick={() => handleReorder(entry.id, "down")}
                                aria-label={`Move token ${entry.token_number} down`}
                              >
                                <ArrowDown className="h-4 w-4" />
                              </Button>
                              <Button
                                size="sm"
                                disabled={isPending}
                                onClick={() => handleCall(entry.id)}
                              >
                                <PhoneCall className="mr-1 h-4 w-4" />
                                Call
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                disabled={isPending}
                                onClick={() => {
                                  setSkipEntry(entry);
                                  setSkipReason("");
                                  setSkipError(null);
                                }}
                              >
                                <SkipForward className="mr-1 h-4 w-4" />
                                Skip
                              </Button>
                            </>
                          )}
                          {canManageQueue && isActive && (
                            <Button
                              size="sm"
                              variant="outline"
                              disabled={isPending}
                              onClick={() => handleComplete(entry.id)}
                            >
                              <CheckCircle2 className="mr-1 h-4 w-4" />
                              Complete
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    )}
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {!canManageQueue && (
        <Alert variant="info">
          You can view the queue board. Call, skip, and reorder actions require the manage OPD
          queue permission.
        </Alert>
      )}

      <Modal
          open={skipEntry !== null}
          onClose={() => {
            setSkipEntry(null);
            setSkipReason("");
            setSkipError(null);
          }}
          title="Skip patient"
        >
          <form className="space-y-4" onSubmit={submitSkip}>
            <p className="text-sm text-muted">
              Provide a short reason for skipping this queue entry.
            </p>
            {skipEntry && (
              <p className="text-sm text-muted">
                Token #{skipEntry.token_number} — {skipEntry.patient_name ?? "Unknown patient"}
              </p>
            )}
            <div>
              <FieldLabel htmlFor="skip-reason">Reason</FieldLabel>
              <Input
                id="skip-reason"
                value={skipReason}
                onChange={(event) => {
                  setSkipReason(event.target.value);
                  setSkipError(null);
                }}
                placeholder="Patient stepped out temporarily"
                maxLength={500}
              />
              {skipError && <p className="mt-1 text-xs text-error">{skipError}</p>}
            </div>
            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setSkipEntry(null);
                  setSkipReason("");
                  setSkipError(null);
                }}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isPending}>
                Skip patient
              </Button>
            </div>
          </form>
        </Modal>
    </div>
  );
}
