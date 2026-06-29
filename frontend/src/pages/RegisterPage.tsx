import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getLegalVersionsRequest, registerTenantRequest } from "@/api/endpoints/platform";
import type { LegalVersions } from "@/api/types/platform";
import { ApiError } from "@/api/errors";
import {
  alertErrorClassName,
  authLinkClassName,
  inputClassName,
  labelClassName,
  labelTextClassName,
  primaryButtonClassName,
  secondaryButtonClassName,
} from "@/components/auth/auth-styles";

const SLUG_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

function slugifyOrganizationName(name: string): string {
  return name
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 100);
}

type WizardStep = 1 | 2 | 3;

export function RegisterPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState<WizardStep>(1);
  const [legal, setLegal] = useState<LegalVersions | null>(null);
  const [legalError, setLegalError] = useState<string | null>(null);

  const [organizationName, setOrganizationName] = useState("");
  const [slug, setSlug] = useState("");
  const [slugTouched, setSlugTouched] = useState(false);
  const [country, setCountry] = useState("IN");
  const [timezone, setTimezone] = useState("Asia/Kolkata");

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [acceptTerms, setAcceptTerms] = useState(false);
  const [acceptPrivacy, setAcceptPrivacy] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    getLegalVersionsRequest()
      .then(setLegal)
      .catch(() => setLegalError("Unable to load legal document versions."));
  }, []);

  useEffect(() => {
    if (!slugTouched && organizationName) {
      setSlug(slugifyOrganizationName(organizationName));
    }
  }, [organizationName, slugTouched]);

  const stepTitle = useMemo(() => {
    if (step === 1) return "Hospital details";
    if (step === 2) return "Administrator account";
    return "Legal acceptance";
  }, [step]);

  function validateStep1(): string | null {
    if (organizationName.trim().length < 2) {
      return "Organization name must be at least 2 characters.";
    }
    if (!SLUG_PATTERN.test(slug) || slug.length < 3) {
      return "Slug must be 3–100 lowercase letters, numbers, or hyphens.";
    }
    return null;
  }

  function validateStep2(): string | null {
    if (!firstName.trim() || !lastName.trim()) {
      return "Administrator first and last name are required.";
    }
    if (!email.trim()) {
      return "Email is required.";
    }
    if (password.length < 8) {
      return "Password must be at least 8 characters.";
    }
    if (password !== confirmPassword) {
      return "Passwords do not match.";
    }
    return null;
  }

  function validateStep3(): string | null {
    if (!acceptTerms || !acceptPrivacy) {
      return "You must accept the Terms of Service and Privacy Policy.";
    }
    return null;
  }

  function handleNext(event: FormEvent) {
    event.preventDefault();
    setError(null);

    const validation =
      step === 1 ? validateStep1() : step === 2 ? validateStep2() : validateStep3();
    if (validation) {
      setError(validation);
      return;
    }

    if (step < 3) {
      setStep((current) => (current + 1) as WizardStep);
      return;
    }

    void submitRegistration();
  }

  async function submitRegistration() {
    setSubmitting(true);
    setError(null);

    try {
      const response = await registerTenantRequest({
        name: organizationName.trim(),
        slug: slug.trim().toLowerCase(),
        email: email.trim().toLowerCase(),
        owner_first_name: firstName.trim(),
        owner_last_name: lastName.trim(),
        owner_password: password,
        accept_terms: acceptTerms,
        accept_privacy_policy: acceptPrivacy,
        country,
        timezone,
        currency: "INR",
      });

      navigate("/login", {
        replace: true,
        state: {
          registeredSlug: response.tenant.slug,
          registeredEmail: email.trim().toLowerCase(),
          registrationMessage: `Hospital registered. Your 14-day trial has started.`,
        },
      });
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Registration failed. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="mx-auto mb-4 flex max-w-md items-center justify-center gap-2">
          {[1, 2, 3].map((stepNumber) => (
            <div key={stepNumber} className="flex flex-1 items-center gap-2">
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-semibold ${
                  stepNumber <= step
                    ? "bg-primary text-white shadow-card"
                    : "border border-border bg-card text-muted"
                }`}
              >
                {stepNumber}
              </div>
              {stepNumber < 3 && (
                <div
                  className={`h-0.5 flex-1 rounded-full ${
                    stepNumber < step ? "bg-primary" : "bg-border-light"
                  }`}
                />
              )}
            </div>
          ))}
        </div>
        <p className="text-xs font-medium uppercase tracking-wide text-muted">Step {step} of 3</p>
        <h1 className="mt-1 text-2xl font-semibold text-foreground">Register your hospital</h1>
        <p className="mt-1 text-sm text-muted">{stepTitle}</p>
      </div>

      <form className="space-y-4" onSubmit={handleNext}>
        {step === 1 && (
          <>
            <label className={labelClassName}>
              <span className={labelTextClassName}>Organization name</span>
              <input
                type="text"
                required
                value={organizationName}
                onChange={(event) => setOrganizationName(event.target.value)}
                className={inputClassName}
                placeholder="Apollo Clinic"
              />
            </label>

            <label className={labelClassName}>
              <span className={labelTextClassName}>Tenant slug</span>
              <input
                type="text"
                required
                value={slug}
                onChange={(event) => {
                  setSlugTouched(true);
                  setSlug(event.target.value.toLowerCase());
                }}
                className={inputClassName}
                placeholder="apollo-clinic"
              />
              <span className="text-xs text-muted">Used for login URL and subdomain</span>
            </label>

            <div className="grid grid-cols-2 gap-3">
              <label className={labelClassName}>
                <span className={labelTextClassName}>Country</span>
                <input
                  type="text"
                  value={country}
                  onChange={(event) => setCountry(event.target.value.toUpperCase())}
                  className={inputClassName}
                />
              </label>
              <label className={labelClassName}>
                <span className={labelTextClassName}>Timezone</span>
                <input
                  type="text"
                  value={timezone}
                  onChange={(event) => setTimezone(event.target.value)}
                  className={inputClassName}
                />
              </label>
            </div>
          </>
        )}

        {step === 2 && (
          <>
            <div className="grid grid-cols-2 gap-3">
              <label className={labelClassName}>
                <span className={labelTextClassName}>First name</span>
                <input
                  type="text"
                  required
                  value={firstName}
                  onChange={(event) => setFirstName(event.target.value)}
                  className={inputClassName}
                />
              </label>
              <label className={labelClassName}>
                <span className={labelTextClassName}>Last name</span>
                <input
                  type="text"
                  required
                  value={lastName}
                  onChange={(event) => setLastName(event.target.value)}
                  className={inputClassName}
                />
              </label>
            </div>

            <label className={labelClassName}>
              <span className={labelTextClassName}>Work email</span>
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
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                className={inputClassName}
              />
            </label>
          </>
        )}

        {step === 3 && (
          <div className="space-y-4 rounded-lg border border-border-light bg-surface p-4 text-sm">
            {legalError && <p className={alertErrorClassName}>{legalError}</p>}
            {legal && (
              <p className="text-muted">
                Terms v{legal.terms_version} · Privacy v{legal.privacy_policy_version}
              </p>
            )}

            <label className="flex items-start gap-2">
              <input
                type="checkbox"
                checked={acceptTerms}
                onChange={(event) => setAcceptTerms(event.target.checked)}
                className="mt-1"
              />
              <span>
                I accept the{" "}
                <Link to="/legal/terms" className={authLinkClassName} target="_blank">
                  Terms of Service
                </Link>
              </span>
            </label>

            <label className="flex items-start gap-2">
              <input
                type="checkbox"
                checked={acceptPrivacy}
                onChange={(event) => setAcceptPrivacy(event.target.checked)}
                className="mt-1"
              />
              <span>
                I accept the{" "}
                <Link to="/legal/privacy" className={authLinkClassName} target="_blank">
                  Privacy Policy
                </Link>
              </span>
            </label>
          </div>
        )}

        {error && (
          <p className={alertErrorClassName} role="alert">
            {error}
          </p>
        )}

        <div className="flex gap-3">
          {step > 1 && (
            <button
              type="button"
              disabled={submitting}
              onClick={() => {
                setError(null);
                setStep((current) => (current - 1) as WizardStep);
              }}
              className={secondaryButtonClassName}
            >
              Back
            </button>
          )}
          <button type="submit" disabled={submitting} className={primaryButtonClassName}>
            {submitting ? "Creating account…" : step === 3 ? "Create hospital account" : "Continue"}
          </button>
        </div>
      </form>

      <p className="text-center text-xs text-muted">
        Already have an account?{" "}
        <Link to="/login" className={authLinkClassName}>
          Sign in
        </Link>
      </p>
    </div>
  );
}
