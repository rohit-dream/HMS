import { FormEvent, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { resetPasswordRequest } from "@/api/endpoints/auth";
import { ApiError } from "@/api/errors";
import {
  alertErrorClassName,
  alertSuccessClassName,
  inputClassName,
  labelClassName,
  labelTextClassName,
  primaryButtonClassName,
} from "@/components/auth/auth-styles";

export function ResetPasswordPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = useMemo(() => searchParams.get("token")?.trim() ?? "", [searchParams]);

  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);

    if (!token) {
      setError("Reset token is missing. Use the link from your email.");
      return;
    }
    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setSubmitting(true);
    try {
      const response = await resetPasswordRequest({ token, newPassword });
      setMessage(response.message);
      setTimeout(() => navigate("/login", { replace: true }), 1500);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to reset password.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-semibold text-slate-900">Reset password</h1>
        <p className="mt-1 text-sm text-muted">Choose a new password for your account.</p>
      </div>

      {!token ? (
        <p className={alertErrorClassName}>Invalid or missing reset token.</p>
      ) : (
        <form className="space-y-4" onSubmit={handleSubmit}>
          <label className={labelClassName}>
            <span className={labelTextClassName}>New password</span>
            <input
              type="password"
              required
              minLength={8}
              autoComplete="new-password"
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
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
            {submitting ? "Updating…" : "Update password"}
          </button>
        </form>
      )}

      <p className="text-center text-xs text-muted">
        <Link to="/login" className="text-primary hover:underline">
          Back to sign in
        </Link>
      </p>
    </div>
  );
}
