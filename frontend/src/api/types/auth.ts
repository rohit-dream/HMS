export interface AuthUserSummary {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  roles: string[];
  tenant_id: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUserSummary;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface MeResponse extends AuthUserSummary {
  permissions: string[];
  staff_id?: string | null;
  location_id?: string | null;
}

export interface LoginCredentials {
  email: string;
  password: string;
  tenantSlug: string;
}

export interface MessageResponse {
  message: string;
}

export interface ForgotPasswordPayload {
  email: string;
  tenantSlug: string;
}

export interface ResetPasswordPayload {
  token: string;
  newPassword: string;
}

export interface AcceptInvitePayload {
  inviteToken: string;
  password: string;
}
