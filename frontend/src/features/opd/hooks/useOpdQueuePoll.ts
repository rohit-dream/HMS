import { useCallback, useEffect, useRef, useState } from "react";
import { pollOpdQueueRequest } from "@/api/endpoints/opd";
import type { OpdQueuePoll } from "@/api/types/opd";

const DEFAULT_POLL_INTERVAL_SECONDS = 5;

export interface UseOpdQueuePollOptions {
  doctorId: string;
  queueDate: string;
  enabled: boolean;
}

export function useOpdQueuePoll({ doctorId, queueDate, enabled }: UseOpdQueuePollOptions) {
  const etagRef = useRef<string | null>(null);
  const pollIntervalRef = useRef(DEFAULT_POLL_INTERVAL_SECONDS);
  const [board, setBoard] = useState<OpdQueuePoll | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [refreshToken, setRefreshToken] = useState(0);

  const invalidate = useCallback(() => {
    etagRef.current = null;
    setRefreshToken((current) => current + 1);
  }, []);

  useEffect(() => {
    if (!enabled || !doctorId) {
      setBoard(null);
      setError(null);
      setIsLoading(false);
      return;
    }

    let cancelled = false;
    let timeoutId: ReturnType<typeof setTimeout> | undefined;
    let firstRequest = true;

    async function tick() {
      if (cancelled) return;

      if (firstRequest) {
        setIsLoading(true);
        firstRequest = false;
      }

      try {
        const result = await pollOpdQueueRequest({
          doctor_id: doctorId,
          date: queueDate,
          ifNoneMatch: etagRef.current ?? undefined,
        });

        if (cancelled) return;

        etagRef.current = result.etag;

        if (result.kind === "updated") {
          setBoard(result.data);
          pollIntervalRef.current = result.data.poll_interval_seconds;
        }

        setError(null);
      } catch (pollError) {
        if (!cancelled) {
          setError(pollError instanceof Error ? pollError : new Error("Queue poll failed"));
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
          timeoutId = setTimeout(tick, pollIntervalRef.current * 1000);
        }
      }
    }

    tick();

    return () => {
      cancelled = true;
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [doctorId, queueDate, enabled, refreshToken]);

  return {
    board,
    isLoading,
    error,
    invalidate,
  };
}
