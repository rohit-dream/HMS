export interface UserListItem {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  status: string;
  roles: string[];
  last_login_at: string | null;
}

export interface UserProfile extends UserListItem {
  tenant_id: string;
  phone: string | null;
  avatar_url: string | null;
  location_id: string | null;
  staff_id: string | null;
  email_verified_at: string | null;
  created_at: string;
}

export interface UserInviteResult extends UserProfile {
  invite_token: string;
  invite_expires_at: string;
}

export interface UserCreatePayload {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone?: string;
  location_id?: string;
  role_codes?: string[];
}

export interface UserInvitePayload {
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  location_id?: string;
  role_codes?: string[];
}

export interface UserUpdatePayload {
  first_name?: string;
  last_name?: string;
  phone?: string;
  status?: string;
}

export interface AssignRolePayload {
  role_code: string;
}
