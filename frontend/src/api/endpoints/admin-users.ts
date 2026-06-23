import { del, get, getPaginated, patch, post } from "@/api/client";
import type {
  AssignRolePayload,
  UserInvitePayload,
  UserInviteResult,
  UserListItem,
  UserProfile,
  UserUpdatePayload,
} from "@/api/types/admin-users";

export async function searchUsersRequest(params: {
  q?: string;
  status?: string;
  page?: number;
  page_size?: number;
}) {
  return getPaginated<UserListItem>("/admin/users", { params });
}

export async function getUserRequest(userId: string): Promise<UserProfile> {
  return get<UserProfile>(`/admin/users/${userId}`);
}

export async function inviteUserRequest(payload: UserInvitePayload): Promise<UserInviteResult> {
  return post<UserInviteResult>("/admin/users/invite", payload);
}

export async function updateUserRequest(
  userId: string,
  payload: UserUpdatePayload,
): Promise<UserProfile> {
  return patch<UserProfile>(`/admin/users/${userId}`, payload);
}

export async function disableUserRequest(userId: string): Promise<UserProfile> {
  return post<UserProfile>(`/admin/users/${userId}/disable`);
}

export async function assignRoleRequest(
  userId: string,
  payload: AssignRolePayload,
): Promise<UserProfile> {
  return post<UserProfile>(`/admin/users/${userId}/roles`, payload);
}

export async function removeRoleRequest(userId: string, roleCode: string): Promise<UserProfile> {
  return del<UserProfile>(`/admin/users/${userId}/roles/${roleCode}`);
}
