import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { forgotPasswordRequest } from "@/api/endpoints/auth";
import { ApiError } from "@/api/errors";
import {
  alertErrorClassName,
  alertSuccessClassName,
  inputClassName,
  labelClassName,
  labelTextClassName,
  primaryButtonClassName,
} from "@/components/auth/auth-styles";
import { DEFAULT_TENANT_SLUG } from "@/lib/constants";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [tenantSlug, setTenantSlug] = useState(DEFAULT_TENANT_SLUG);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setSubmitting(true);

    try {
      const response = await forgotPasswordRequest({ email, tenantSlug });
      setMessage(response.message);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to process request.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-semibold text-slate-900">Forgot password</h1>
        <p className="mt-1 text-sm text-muted">
          We will email a reset link if the account exists for your tenant.
        </p>
      </div>

      <form className="space-y-4" onSubmit={handleSubmit}>
        <label className={labelClassName}>
          <span className={labelTextClassName}>Tenant slug</span>
          <input
            type="text"
            required
            value={tenantSlug}
            onChange={(event) => setTenantSlug(event.target.value)}
            className={inputClassName}
          />
        </label>

        <label className={labelClassName}>
          <span className={labelTextClassName}>Email</span>
          <input
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
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
          {submitting ? "Sending…" : "Send reset link"}
        </button>
      </form>

      <p className="text-center text-xs text-muted">
        <Link to="/login" className="text-primary hover:underline">
          Back to sign in
        </Link>
      </p>
    </div>
  );
}
