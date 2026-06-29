import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { resendVerificationRequest, verifyEmailRequest } from "@/api/endpoints/auth";
import { ApiError } from "@/api/errors";
import {
  alertErrorClassName,
  alertSuccessClassName,
  authLinkClassName,
  primaryButtonClassName,
} from "@/components/auth/auth-styles";
import { useAuth } from "@/providers/AuthProvider";

type VerifyState = "idle" | "loading" | "success" | "error";

export function VerifyEmailPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const token = useMemo(() => new URLSearchParams(window.location.search).get("token")?.trim() ?? "", []);

  const [verifyState, setVerifyState] = useState<VerifyState>(token ? "loading" : "idle");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [resendMessage, setResendMessage] = useState<string | null>(null);
  const [resending, setResending] = useState(false);

  useEffect(() => {
    if (!token) {
      return;
    }

    let cancelled = false;
    void (async () => {
      try {
        const response = await verifyEmailRequest(token);
        if (!cancelled) {
          setMessage(response.message);
          setVerifyState("success");
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Verification failed.");
          setVerifyState("error");
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [token]);

  async function handleResend() {
    setResendMessage(null);
    setError(null);
    setResending(true);
    try {
      const response = await resendVerificationRequest();
      setResendMessage(response.message);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to resend verification email.");
    } finally {
      setResending(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-semibold text-foreground">Verify email</h1>
        <p className="mt-1 text-sm text-muted">
          {token ? "Confirming your email address…" : "Request a new verification link if needed."}
        </p>
      </div>

      {token && verifyState === "loading" && (
        <p className="text-center text-sm text-muted">Verifying token…</p>
      )}

      {message && (
        <p className={alertSuccessClassName} role="status">
          {message}
        </p>
      )}

      {error && (
        <p className={alertErrorClassName} role="alert">
          {error}
        </p>
      )}

      {!token && !isLoading && isAuthenticated && (
        <div className="space-y-3">
          <button
            type="button"
            onClick={() => void handleResend()}
            disabled={resending}
            className={primaryButtonClassName}
          >
            {resending ? "Sending…" : "Resend verification email"}
          </button>
          {resendMessage && (
            <p className={alertSuccessClassName} role="status">
              {resendMessage}
            </p>
          )}
        </div>
      )}

      {!token && !isAuthenticated && !isLoading && (
        <p className="text-center text-sm text-muted">
          Sign in to resend a verification email, or open the link from your inbox.
        </p>
      )}

      <p className="text-center text-xs text-muted">
        <Link to="/login" className={authLinkClassName}>
          Back to sign in
        </Link>
        {isAuthenticated && (
          <>
            {" "}
            ·{" "}
            <Link to="/dashboard" className={authLinkClassName}>
              Go to dashboard
            </Link>
          </>
        )}
      </p>
    </div>
  );
}
