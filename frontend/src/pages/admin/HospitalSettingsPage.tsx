import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  bulkUpdateSettingsRequest,
  getHospitalProfileRequest,
  listSettingsRequest,
  updateHospitalProfileRequest,
} from "@/api/endpoints/hospital";
import { ApiError } from "@/api/errors";
import { AdminPageFrame, FormPageLayout, FormSection } from "@/components/enterprise";
import { Button, FieldLabel, Input, Select, useToast } from "@/components/ui";
import { DATE_FORMAT_OPTIONS } from "@/lib/admin-constants";

function settingsMap(settings: { setting_key: string; setting_value: Record<string, unknown> }[]) {
  return Object.fromEntries(settings.map((item) => [item.setting_key, item.setting_value]));
}

export function HospitalSettingsPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
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
      toast.success("Hospital profile saved.");
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : "Failed to save profile.");
    },
  });

  const settingsMutation = useMutation({
    mutationFn: bulkUpdateSettingsRequest,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["hospital", "settings"] });
      toast.success("System configuration saved.");
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : "Failed to save system configuration.");
    },
  });

  const isLoading = profileQuery.isLoading || settingsQuery.isLoading;
  const isSaving = profileMutation.isPending || settingsMutation.isPending;

  function handleProfileSubmit(event: FormEvent) {
    event.preventDefault();
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
    const parsedTax = Number.parseFloat(taxRate);
    if (Number.isNaN(parsedTax) || parsedTax < 0) {
      toast.error("Tax rate must be a valid non-negative number.");
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
    <AdminPageFrame
      title="Hospital configuration"
      description="Organization profile, regional settings, and system defaults for your tenant."
    >
      <FormPageLayout>
        <form className="space-y-8" onSubmit={handleProfileSubmit}>
          <FormSection title="Organization profile" description="Public hospital identity and contact information">

        <FieldLabel htmlFor="hospital-name" label="Hospital name">
          <Input id="hospital-name" value={name} onChange={(e) => setName(e.target.value)} required />
        </FieldLabel>

        <div className="grid gap-4 md:grid-cols-2">
          <FieldLabel htmlFor="hospital-phone" label="Phone">
            <Input id="hospital-phone" value={phone} onChange={(e) => setPhone(e.target.value)} />
          </FieldLabel>
          <FieldLabel htmlFor="hospital-tax" label="Tax registration no.">
            <Input
              id="hospital-tax"
              value={taxRegistrationNo}
              onChange={(e) => setTaxRegistrationNo(e.target.value)}
            />
          </FieldLabel>
        </div>

        <FieldLabel htmlFor="hospital-address" label="Address">
          <Input id="hospital-address" value={addressLine1} onChange={(e) => setAddressLine1(e.target.value)} />
        </FieldLabel>

        <div className="grid gap-4 md:grid-cols-3">
          <FieldLabel htmlFor="hospital-city" label="City">
            <Input id="hospital-city" value={city} onChange={(e) => setCity(e.target.value)} />
          </FieldLabel>
          <FieldLabel htmlFor="hospital-state" label="State">
            <Input id="hospital-state" value={state} onChange={(e) => setState(e.target.value)} />
          </FieldLabel>
          <FieldLabel htmlFor="hospital-postal" label="Postal code">
            <Input id="hospital-postal" value={postalCode} onChange={(e) => setPostalCode(e.target.value)} />
          </FieldLabel>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <FieldLabel htmlFor="hospital-timezone" label="Timezone">
            <Input id="hospital-timezone" value={timezone} onChange={(e) => setTimezone(e.target.value)} />
          </FieldLabel>
          <FieldLabel htmlFor="hospital-currency" label="Currency">
            <Input
              id="hospital-currency"
              value={currency}
              maxLength={3}
              onChange={(e) => setCurrency(e.target.value.toUpperCase())}
            />
          </FieldLabel>
        </div>
          </FormSection>

        <Button type="submit" fullWidth disabled={isSaving}>
          {profileMutation.isPending ? "Saving…" : "Save profile"}
        </Button>
        </form>

        <form className="space-y-8" onSubmit={handleSystemSubmit}>
          <FormSection title="System configuration" description="Billing defaults, MRN prefix, and display formats">

        <div className="grid gap-4 sm:grid-cols-2">
          <FieldLabel htmlFor="tax-rate" label="Default tax rate (%)">
            <Input
              id="tax-rate"
              type="number"
              min={0}
              step={0.01}
              value={taxRate}
              onChange={(e) => setTaxRate(e.target.value)}
            />
          </FieldLabel>
          <FieldLabel htmlFor="mrn-prefix" label="MRN prefix">
            <Input id="mrn-prefix" value={mrnPrefix} onChange={(e) => setMrnPrefix(e.target.value)} />
          </FieldLabel>
        </div>

        <FieldLabel htmlFor="date-format" label="Date format">
          <Select id="date-format" value={dateFormat} onChange={(e) => setDateFormat(e.target.value)}>
            {DATE_FORMAT_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </Select>
        </FieldLabel>

        <label className="flex items-center gap-2 text-sm text-foreground/90">
          <input
            type="checkbox"
            checked={taxInclusive}
            onChange={(e) => setTaxInclusive(e.target.checked)}
          />
          Tax-inclusive pricing
        </label>
          </FormSection>

        <Button type="submit" fullWidth disabled={isSaving}>
          {settingsMutation.isPending ? "Saving…" : "Save system configuration"}
        </Button>
        </form>
      </FormPageLayout>
    </AdminPageFrame>
  );
}
