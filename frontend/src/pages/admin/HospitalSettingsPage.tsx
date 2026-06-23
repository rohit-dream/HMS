import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  bulkUpdateSettingsRequest,
  getHospitalProfileRequest,
  listSettingsRequest,
  updateHospitalProfileRequest,
} from "@/api/endpoints/hospital";
import { ApiError } from "@/api/errors";
import {
  alertErrorClassName,
  alertSuccessClassName,
  inputClassName,
  labelClassName,
  labelTextClassName,
  primaryButtonClassName,
} from "@/components/auth/auth-styles";
import { DATE_FORMAT_OPTIONS } from "@/lib/admin-constants";

function settingsMap(settings: { setting_key: string; setting_value: Record<string, unknown> }[]) {
  return Object.fromEntries(settings.map((item) => [item.setting_key, item.setting_value]));
}

export function HospitalSettingsPage() {
  const queryClient = useQueryClient();
  const profileQuery = useQuery({ queryKey: ["hospital", "profile"], queryFn: getHospitalProfileRequest });
  const settingsQuery = useQuery({ queryKey: ["hospital", "settings"], queryFn: listSettingsRequest });

  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [addressLine1, setAddressLine1] = useState("");
  const [city, setCity] = useState("");
  const [state, setState] = useState("");
  const [postalCode, setPostalCode] = useState("");
  const [taxRegistrationNo, setTaxRegistrationNo] = useState("");
  const [timezone, setTimezone] = useState("");
  const [currency, setCurrency] = useState("");

  const [taxRate, setTaxRate] = useState("18");
  const [taxInclusive, setTaxInclusive] = useState(false);
  const [mrnPrefix, setMrnPrefix] = useState("MRN");
  const [dateFormat, setDateFormat] = useState<string>("DD/MM/YYYY");

  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (!profileQuery.data) return;
    const profile = profileQuery.data;
    setName(profile.name);
    setPhone(profile.phone ?? "");
    setAddressLine1(profile.address_line1 ?? "");
    setCity(profile.city ?? "");
    setState(profile.state ?? "");
    setPostalCode(profile.postal_code ?? "");
    setTaxRegistrationNo(profile.tax_registration_no ?? "");
    setTimezone(profile.timezone);
    setCurrency(profile.currency);
  }, [profileQuery.data]);

  useEffect(() => {
    if (!settingsQuery.data) return;
    const map = settingsMap(settingsQuery.data);
    const billing = map.billing as { tax_rate?: number; tax_inclusive_pricing?: boolean } | undefined;
    const clinical = map.clinical as { mrn_prefix?: string } | undefined;
    const system = map.system as { date_format?: string } | undefined;
    if (billing?.tax_rate !== undefined) setTaxRate(String(billing.tax_rate));
    if (billing?.tax_inclusive_pricing !== undefined) setTaxInclusive(billing.tax_inclusive_pricing);
    if (clinical?.mrn_prefix) setMrnPrefix(clinical.mrn_prefix);
    if (system?.date_format) setDateFormat(system.date_format);
  }, [settingsQuery.data]);

  const profileMutation = useMutation({
    mutationFn: updateHospitalProfileRequest,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["hospital", "profile"] });
      setSuccess("Hospital profile saved.");
      setError(null);
    },
    onError: (err) => {
      setSuccess(null);
      setError(err instanceof ApiError ? err.message : "Failed to save profile.");
    },
  });

  const settingsMutation = useMutation({
    mutationFn: bulkUpdateSettingsRequest,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["hospital", "settings"] });
      setSuccess("System configuration saved.");
      setError(null);
    },
    onError: (err) => {
      setSuccess(null);
      setError(err instanceof ApiError ? err.message : "Failed to save system configuration.");
    },
  });

  const isLoading = profileQuery.isLoading || settingsQuery.isLoading;
  const isSaving = profileMutation.isPending || settingsMutation.isPending;

  function handleProfileSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSuccess(null);
    profileMutation.mutate({
      name: name.trim(),
      phone: phone.trim() || undefined,
      address_line1: addressLine1.trim() || undefined,
      city: city.trim() || undefined,
      state: state.trim() || undefined,
      postal_code: postalCode.trim() || undefined,
      tax_registration_no: taxRegistrationNo.trim() || undefined,
      timezone: timezone.trim() || undefined,
      currency: currency.trim().toUpperCase() || undefined,
    });
  }

  function handleSystemSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSuccess(null);
    const parsedTax = Number.parseFloat(taxRate);
    if (Number.isNaN(parsedTax) || parsedTax < 0) {
      setError("Tax rate must be a valid non-negative number.");
      return;
    }
    settingsMutation.mutate({
      settings: {
        billing: { tax_rate: parsedTax, tax_inclusive_pricing: taxInclusive },
        clinical: { mrn_prefix: mrnPrefix.trim() || "MRN" },
        system: { date_format: dateFormat },
      },
    });
  }

  if (isLoading) {
    return <p className="text-sm text-muted">Loading hospital settings…</p>;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <div>
        <h2 className="text-2xl font-semibold text-slate-900">Hospital settings</h2>
        <p className="mt-1 text-sm text-muted">Organization profile and system configuration (FR-ADM-004).</p>
      </div>

      {error && <p className={alertErrorClassName}>{error}</p>}
      {success && <p className={alertSuccessClassName}>{success}</p>}

      <form className="space-y-4 rounded-lg border border-border bg-white p-6" onSubmit={handleProfileSubmit}>
        <h3 className="text-lg font-medium text-slate-900">Organization profile</h3>

        <label className={labelClassName}>
          <span className={labelTextClassName}>Hospital name</span>
          <input className={inputClassName} value={name} onChange={(e) => setName(e.target.value)} required />
        </label>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className={labelClassName}>
            <span className={labelTextClassName}>Phone</span>
            <input className={inputClassName} value={phone} onChange={(e) => setPhone(e.target.value)} />
          </label>
          <label className={labelClassName}>
            <span className={labelTextClassName}>Tax registration no.</span>
            <input
              className={inputClassName}
              value={taxRegistrationNo}
              onChange={(e) => setTaxRegistrationNo(e.target.value)}
            />
          </label>
        </div>

        <label className={labelClassName}>
          <span className={labelTextClassName}>Address</span>
          <input
            className={inputClassName}
            value={addressLine1}
            onChange={(e) => setAddressLine1(e.target.value)}
          />
        </label>

        <div className="grid gap-4 sm:grid-cols-3">
          <label className={labelClassName}>
            <span className={labelTextClassName}>City</span>
            <input className={inputClassName} value={city} onChange={(e) => setCity(e.target.value)} />
          </label>
          <label className={labelClassName}>
            <span className={labelTextClassName}>State</span>
            <input className={inputClassName} value={state} onChange={(e) => setState(e.target.value)} />
          </label>
          <label className={labelClassName}>
            <span className={labelTextClassName}>Postal code</span>
            <input
              className={inputClassName}
              value={postalCode}
              onChange={(e) => setPostalCode(e.target.value)}
            />
          </label>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className={labelClassName}>
            <span className={labelTextClassName}>Timezone</span>
            <input className={inputClassName} value={timezone} onChange={(e) => setTimezone(e.target.value)} />
          </label>
          <label className={labelClassName}>
            <span className={labelTextClassName}>Currency</span>
            <input
              className={inputClassName}
              value={currency}
              maxLength={3}
              onChange={(e) => setCurrency(e.target.value.toUpperCase())}
            />
          </label>
        </div>

        <button type="submit" disabled={isSaving} className={primaryButtonClassName}>
          {profileMutation.isPending ? "Saving…" : "Save profile"}
        </button>
      </form>

      <form className="space-y-4 rounded-lg border border-border bg-white p-6" onSubmit={handleSystemSubmit}>
        <h3 className="text-lg font-medium text-slate-900">System configuration</h3>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className={labelClassName}>
            <span className={labelTextClassName}>Default tax rate (%)</span>
            <input
              type="number"
              min={0}
              step={0.01}
              className={inputClassName}
              value={taxRate}
              onChange={(e) => setTaxRate(e.target.value)}
            />
          </label>
          <label className={labelClassName}>
            <span className={labelTextClassName}>MRN prefix</span>
            <input className={inputClassName} value={mrnPrefix} onChange={(e) => setMrnPrefix(e.target.value)} />
          </label>
        </div>

        <label className={labelClassName}>
          <span className={labelTextClassName}>Date format</span>
          <select
            className={inputClassName}
            value={dateFormat}
            onChange={(e) => setDateFormat(e.target.value)}
          >
            {DATE_FORMAT_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>

        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={taxInclusive}
            onChange={(e) => setTaxInclusive(e.target.checked)}
          />
          Tax-inclusive pricing
        </label>

        <button type="submit" disabled={isSaving} className={primaryButtonClassName}>
          {settingsMutation.isPending ? "Saving…" : "Save system configuration"}
        </button>
      </form>
    </div>
  );
}
