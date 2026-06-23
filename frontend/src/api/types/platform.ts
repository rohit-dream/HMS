export interface LegalVersions {
  terms_version: string;
  privacy_policy_version: string;
  terms_url: string;
  privacy_policy_url: string;
}

export interface TenantRegisterPayload {
  name: string;
  slug: string;
  email: string;
  owner_first_name: string;
  owner_last_name: string;
  owner_password: string;
  accept_terms: boolean;
  accept_privacy_policy: boolean;
  country?: string;
  timezone?: string;
  currency?: string;
}

export interface TenantSummary {
  id: string;
  name: string;
  slug: string;
  subdomain: string | null;
  status: string;
  email: string;
}

export interface TenantRegisterResponse {
  tenant: TenantSummary;
  trial_ends_at: string | null;
}
