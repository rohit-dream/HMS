export interface HospitalProfile {
  id: string;
  name: string;
  slug: string;
  email: string;
  phone: string | null;
  logo_url: string | null;
  address_line1: string | null;
  address_line2: string | null;
  city: string | null;
  state: string | null;
  postal_code: string | null;
  country: string;
  tax_registration_no: string | null;
  timezone: string;
  currency: string;
  status: string;
}

export interface HospitalProfileUpdate {
  name?: string;
  phone?: string;
  logo_url?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  tax_registration_no?: string;
  timezone?: string;
  currency?: string;
}

export interface HospitalLocation {
  id: string;
  tenant_id: string;
  name: string;
  code: string;
  is_primary: boolean;
  address_line1: string | null;
  city: string | null;
  state: string | null;
  phone: string | null;
  is_active: boolean;
}

export interface LocationCreate {
  name: string;
  code: string;
  is_primary?: boolean;
  address_line1?: string;
  city?: string;
  state?: string;
  phone?: string;
}

export interface LocationUpdate {
  name?: string;
  address_line1?: string;
  city?: string;
  state?: string;
  phone?: string;
  is_primary?: boolean;
  is_active?: boolean;
}

export interface TenantSetting {
  setting_key: string;
  setting_value: Record<string, unknown>;
  description: string | null;
}

export interface SettingsBulkUpdate {
  settings: Record<string, Record<string, unknown>>;
}

export interface BillingSettings {
  tax_rate?: number;
  tax_inclusive_pricing?: boolean;
  invoice_prefix?: string;
}

export interface ClinicalSettings {
  mrn_prefix?: string;
}

export interface SystemSettings {
  date_format?: string;
}
