import { useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { SESSION_IDLE_TIMEOUT_MS } from "@/lib/constants";
import { useIdleTimeout } from "@/hooks/useIdleTimeout";
import { useAuth } from "@/providers/AuthProvider";

/**
 * MVP-034 / FR-AUTH-006 — signs the user out after inactivity and returns to login.
 */
export function SessionIdleMonitor() {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const handlingTimeoutRef = useRef(false);

  const handleTimeout = useCallback(async () => {
    if (handlingTimeoutRef.current) {
      return;
    }
    handlingTimeoutRef.current = true;
    try {
      await logout();
      navigate("/login", { replace: true, state: { reason: "session_expired" } });
    } finally {
      handlingTimeoutRef.current = false;
    }
  }, [logout, navigate]);

  useIdleTimeout({
    enabled: isAuthenticated,
    timeoutMs: SESSION_IDLE_TIMEOUT_MS,
    onTimeout: () => {
      void handleTimeout();
    },
  });

  return null;
}
