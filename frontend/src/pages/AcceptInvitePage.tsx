import { FormEvent, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { acceptInviteRequest } from "@/api/endpoints/auth";
import { ApiError } from "@/api/errors";
import {
  alertErrorClassName,
  alertSuccessClassName,
  authLinkClassName,
  inputClassName,
  labelClassName,
  labelTextClassName,
  primaryButtonClassName,
} from "@/components/auth/auth-styles";
import { resolvePostAuthPath } from "@/lib/role-landing";
import { useAuth } from "@/providers/AuthProvider";

export function AcceptInvitePage() {
  const navigate = useNavigate();
  const { activateSession } = useAuth();
  const [searchParams] = useSearchParams();
  const inviteToken = useMemo(() => searchParams.get("token")?.trim() ?? "", [searchParams]);
  const tenantSlug = useMemo(() => searchParams.get("tenant")?.trim() ?? "", [searchParams]);

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);

    if (!inviteToken) {
      setError("Invite token is missing. Use the link from your invitation email.");
      return;
    }
    if (!tenantSlug) {
      setError("Hospital identifier is missing from the invite link.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setSubmitting(true);
    try {
      const response = await acceptInviteRequest({ inviteToken, password });
      const me = await activateSession(response.access_token, tenantSlug);
      setMessage("Your account is active. Redirecting to your workspace…");
      setTimeout(
        () => navigate(resolvePostAuthPath(undefined, me.roles), { replace: true }),
        1200,
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to accept invitation.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-semibold text-foreground">Accept invitation</h1>
        <p className="mt-1 text-sm text-muted">
          Set a password to activate your {tenantSlug ? `${tenantSlug} ` : ""}account.
        </p>
      </div>

      {!inviteToken || !tenantSlug ? (
        <p className={alertErrorClassName}>
          This invitation link is invalid or incomplete. Ask your administrator to resend the invite.
        </p>
      ) : (
        <form className="space-y-4" onSubmit={handleSubmit}>
          <label className={labelClassName}>
            <span className={labelTextClassName}>Password</span>
            <input
              type="password"
              required
              minLength={8}
              autoComplete="new-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className={inputClassName}
            />
          </label>

          <label className={labelClassName}>
            <span className={labelTextClassName}>Confirm password</span>
            <input
              type="password"
              required
              minLength={8}
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              className={inputClassName}
            />
          </label>

          {error && (
            <p className={alertErrorClassName} role="alert">
              {error}
            </p>
          )}
          {message && (
            <p className={alertSuccessClassName} role="status">
              {message}
            </p>
          )}

          <button type="submit" disabled={submitting} className={primaryButtonClassName}>
            {submitting ? "Activating…" : "Activate account"}
          </button>
        </form>
      )}

      <p className="text-center text-xs text-muted">
        <Link to="/login" className={authLinkClassName}>
          Back to sign in
        </Link>
      </p>
    </div>
  );
}
