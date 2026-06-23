import { useEffect, useRef } from "react";

const ACTIVITY_EVENTS = ["mousedown", "keydown", "scroll", "touchstart", "click"] as const;

export interface UseIdleTimeoutOptions {
  enabled: boolean;
  timeoutMs: number;
  onTimeout: () => void;
}

/**
 * Invokes onTimeout after timeoutMs without user activity.
 * Resets on common interaction events and re-checks elapsed idle time when the tab becomes visible.
 */
export function useIdleTimeout({ enabled, timeoutMs, onTimeout }: UseIdleTimeoutOptions): void {
  const onTimeoutRef = useRef(onTimeout);
  const lastActivityRef = useRef(Date.now());

  useEffect(() => {
    onTimeoutRef.current = onTimeout;
  }, [onTimeout]);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    let timeoutId: ReturnType<typeof setTimeout> | undefined;

    const fireTimeout = () => {
      onTimeoutRef.current();
    };

    const scheduleTimeout = () => {
      if (timeoutId !== undefined) {
        clearTimeout(timeoutId);
      }
      const elapsed = Date.now() - lastActivityRef.current;
      const remaining = Math.max(timeoutMs - elapsed, 0);
      timeoutId = setTimeout(fireTimeout, remaining);
    };

    const recordActivity = () => {
      lastActivityRef.current = Date.now();
      scheduleTimeout();
    };

    const handleVisibilityChange = () => {
      if (document.visibilityState !== "visible") {
        return;
      }
      const elapsed = Date.now() - lastActivityRef.current;
      if (elapsed >= timeoutMs) {
        fireTimeout();
        return;
      }
      scheduleTimeout();
    };

    lastActivityRef.current = Date.now();
    scheduleTimeout();

    for (const event of ACTIVITY_EVENTS) {
      window.addEventListener(event, recordActivity, { passive: true });
    }
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      if (timeoutId !== undefined) {
        clearTimeout(timeoutId);
      }
      for (const event of ACTIVITY_EVENTS) {
        window.removeEventListener(event, recordActivity);
      }
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [enabled, timeoutMs]);
}
