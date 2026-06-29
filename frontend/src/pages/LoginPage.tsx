import { FormEvent, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { ApiError } from "@/api/errors";
import {
  alertErrorClassName,
  alertSuccessClassName,
  alertWarningClassName,
  authLinkClassName,
  inputClassName,
  labelClassName,
  labelTextClassName,
  primaryButtonClassName,
} from "@/components/auth/auth-styles";
import { DEFAULT_TENANT_SLUG } from "@/lib/constants";
import { resolvePostAuthPath } from "@/lib/role-landing";
import { useAuth } from "@/providers/AuthProvider";

export function LoginPage() {
  const { login, isLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
  const sessionExpired =
    (location.state as { reason?: string } | null)?.reason === "session_expired";
  const registrationState = location.state as {
    registeredSlug?: string;
    registeredEmail?: string;
    registrationMessage?: string;
  } | null;

  const [email, setEmail] = useState(registrationState?.registeredEmail ?? "");
  const [password, setPassword] = useState("");
  const [tenantSlug, setTenantSlug] = useState(
    registrationState?.registeredSlug ?? DEFAULT_TENANT_SLUG,
  );
  const successMessage = registrationState?.registrationMessage ?? null;
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const me = await login({ email, password, tenantSlug });
      navigate(resolvePostAuthPath(from, me.roles), { replace: true });
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Login failed. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-shell">
      <div className="text-center">
        <h1 className="text-2xl font-semibold text-foreground">Sign in</h1>
        <p className="mt-1.5 text-sm text-muted">Use your hospital tenant credentials</p>
      </div>

      {sessionExpired && (
        <p className={alertWarningClassName} role="status">
          Your session expired due to inactivity. Please sign in again.
        </p>
      )}

      {successMessage && (
        <p className={alertSuccessClassName} role="status">
          {successMessage}
        </p>
      )}

      <form className="space-y-4" onSubmit={handleSubmit}>
        <label className={labelClassName}>
          <span className={labelTextClassName}>Tenant slug</span>
          <input
            type="text"
            required
            autoComplete="organization"
            value={tenantSlug}
            onChange={(event) => setTenantSlug(event.target.value)}
            className={inputClassName}
            placeholder="apollo-clinic"
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

        <label className={labelClassName}>
          <span className={labelTextClassName}>Password</span>
          <input
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className={inputClassName}
          />
        </label>

        {error && (
          <p className={alertErrorClassName} role="alert">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={submitting || isLoading}
          className={primaryButtonClassName}
        >
          {submitting ? "Signing in…" : "Sign in"}
        </button>
      </form>

      <p className="text-center text-xs text-muted">
        <Link to="/forgot-password" className={authLinkClassName}>
          Forgot password?
        </Link>
        {" · "}
        <Link to="/register" className={authLinkClassName}>
          Register hospital
        </Link>
      </p>
    </div>
  );
}
