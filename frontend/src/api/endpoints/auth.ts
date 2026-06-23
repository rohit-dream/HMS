import { get, post, postNoContent } from "@/api/client";
import { setTenantSlug } from "@/api/auth-session";
import type {
  ForgotPasswordPayload,
  LoginCredentials,
  LoginResponse,
  MeResponse,
  MessageResponse,
  ResetPasswordPayload,
  TokenResponse,
} from "@/api/types/auth";

export type {
  AuthUserSummary,
  ForgotPasswordPayload,
  LoginCredentials,
  LoginResponse,
  MeResponse,
  MessageResponse,
  ResetPasswordPayload,
  TokenResponse,
} from "@/api/types/auth";

export async function loginRequest(credentials: LoginCredentials): Promise<LoginResponse> {
  return post<LoginResponse>("/auth/login", {
    email: credentials.email,
    password: credentials.password,
  });
}

export async function refreshRequest(): Promise<TokenResponse> {
  return post<TokenResponse>(
    "/auth/refresh",
    {},
    {
      headers: {
        Origin: window.location.origin,
      },
    },
  );
}

export async function logoutRequest(): Promise<void> {
  await postNoContent("/auth/logout");
}

export async function getMeRequest(): Promise<MeResponse> {
  return get<MeResponse>("/auth/me");
}

export async function forgotPasswordRequest(
  payload: ForgotPasswordPayload,
): Promise<MessageResponse> {
  setTenantSlug(payload.tenantSlug);
  return post<MessageResponse>("/auth/forgot-password", { email: payload.email });
}

export async function resetPasswordRequest(
  payload: ResetPasswordPayload,
): Promise<MessageResponse> {
  return post<MessageResponse>("/auth/reset-password", {
    token: payload.token,
    new_password: payload.newPassword,
  });
}

export async function verifyEmailRequest(token: string): Promise<MessageResponse> {
  return post<MessageResponse>("/auth/verify-email", { token });
}

export async function resendVerificationRequest(): Promise<MessageResponse> {
  return post<MessageResponse>("/auth/resend-verification");
}
