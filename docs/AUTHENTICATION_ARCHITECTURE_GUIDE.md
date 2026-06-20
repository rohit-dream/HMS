# Authentication Architecture Guide

## Multi-Tenant Hospital Management SaaS Platform

| Field | Value |
|-------|-------|
| **Document Version** | 1.0 |
| **Status** | Active |
| **Last Updated** | June 2026 |
| **Author** | Security Architecture |
| **Audience** | Engineering, Security, Compliance |
| **Related Documents** | SECURITY_ARCHITECTURE.md, RBAC_DESIGN.md, API_DESIGN.md §3, MULTI_TENANT_DESIGN.md, SYSTEM_ARCHITECTURE.md §6, IMPLEMENTATION_PLAN.md §6 |

---

## Executive Summary

The HMS SaaS platform uses **stateless JWT access tokens** for API authentication combined with **server-side refresh token sessions** for long-lived browser access. Every authenticated request is bound to a **single tenant context** derived from the JWT — never from client-supplied body or query parameters.

### Architectural Principles

| Principle | Implementation |
|-----------|----------------|
| **Defence in depth** | WAF → rate limit → JWT validation → tenant gate → RBAC → RLS |
| **Least privilege** | Permissions resolved server-side; roles in JWT for UI only |
| **Fail secure** | Invalid or missing auth → 401; suspended tenant → 403 |
| **Tenant binding** | `tenant_id` in JWT is authoritative for all data access |
| **No secrets in tokens** | Permissions and PHI never embedded in JWT |
| **Auditability** | Login, logout, lockout, reset, and impersonation are logged |

### Authoritative Design Decision (Documentation Alignment)

Some older diagrams in `SYSTEM_ARCHITECTURE.md` show `permissions` inside the JWT payload. **This guide and `SECURITY_ARCHITECTURE.md` §5.2 are authoritative:**

| Claim | In JWT? | Resolved How |
|-------|---------|--------------|
| `sub` (user ID) | ✅ Yes | Signed claim |
| `tenant_id` | ✅ Yes | Signed claim |
| `roles[]` | ✅ Yes | UI navigation hints only |
| `permissions[]` | ❌ **No** | Redis-cached DB lookup per request |
| `jti` | ✅ Yes | Revocation denylist |

Permissions are returned on `GET /auth/me` for frontend guards but are **re-validated server-side** on every protected API call.

---

## Authentication Topology

```mermaid
flowchart TB
    subgraph Client["Browser (React SPA)"]
        MEM["Access Token<br/>(memory only)"]
        COOKIE["Refresh Token<br/>(HttpOnly cookie)"]
    end

    subgraph Edge["Edge"]
        WAF["AWS WAF"]
        RL["Rate Limiter<br/>10 req/min auth"]
    end

    subgraph API["FastAPI"]
        AUTH["Auth Middleware<br/>JWT RS256 verify"]
        TENANT["Tenant Middleware<br/>subscription gate"]
        RBAC["RBAC Middleware<br/>permission check"]
    end

    subgraph Data["Data Stores"]
        PG[("PostgreSQL<br/>users · sessions · audit")]
        REDIS[("Redis<br/>jti denylist · permissions cache")]
    end

    Client -->|HTTPS Bearer| WAF --> RL --> AUTH
    AUTH --> TENANT --> RBAC
    AUTH --> PG
    AUTH --> REDIS
    Client -->|Cookie refresh| AUTH
```

---

## 1. Login Flow

Login authenticates a **tenant-scoped user** using email + password. The tenant is resolved from the **subdomain** (or host header) before credentials are checked — the same email may exist in multiple tenants as separate user records.

### 1.1 Entry Points

| Entry Point | URL Pattern | Use Case |
|-------------|-------------|----------|
| Tenant login | `https://{subdomain}.platform.com/login` | Daily staff access |
| Local dev | `http://localhost:5173/login` + tenant context | Development |

### 1.2 Login Sequence

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant FE as React SPA
    participant API as POST /api/v1/auth/login
    participant DB as PostgreSQL
    participant Redis as Redis

    U->>FE: Enter email + password
    FE->>API: POST /auth/login<br/>Host: apollo.platform.com

    API->>API: Rate limit check (IP)
    API->>DB: Resolve tenant from subdomain "apollo"
    Note over API,DB: SELECT id FROM platform.tenants<br/>WHERE subdomain = 'apollo'<br/>AND status IN ('trial','active','past_due')

    alt Tenant not found or blocked
        API-->>FE: 403 tenant_suspended / not found
    end

    API->>DB: Find user by (tenant_id, email)
    Note over API,DB: core.users WHERE tenant_id = X AND email = Y

    alt User not found OR wrong password
        API->>DB: Increment failed_login_attempts
        API->>DB: audit_log(action=login_failed)
        API-->>FE: 401 Invalid credentials
    else Account locked (failed_login_attempts >= 5)
        API-->>FE: 423 Locked until locked_until
    else Valid password
        API->>API: Verify password_hash (bcrypt/Argon2)
        API->>API: Build access JWT (RS256)
        API->>API: Generate opaque refresh token
        API->>DB: INSERT core.user_sessions (refresh_token_hash)
        API->>DB: Reset failed_login_attempts; set last_login_at
        API->>DB: audit_log(action=login)
        API-->>FE: 200 { access_token, expires_in, user }
        API-->>FE: Set-Cookie: refresh_token (HttpOnly, Secure, SameSite=Strict)
        FE->>FE: Store access_token in memory (NOT localStorage)
        FE->>FE: Redirect to role-based dashboard
    end
```

### 1.3 Login Request Example

**Request:**

```http
POST /api/v1/auth/login HTTP/1.1
Host: apollo.platform.com
Content-Type: application/json

{
  "email": "doctor@apollo.com",
  "password": "SecurePass@123"
}
```

**Success response (200):**

```json
{
  "data": {
    "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "email": "doctor@apollo.com",
      "first_name": "Vikram",
      "last_name": "Patel",
      "roles": ["doctor"],
      "tenant_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7"
    }
  },
  "meta": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-06-17T10:30:00Z",
    "tenant_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7"
  },
  "errors": null
}
```

**Response header:**

```http
Set-Cookie: refresh_token=<opaque>; HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth; Max-Age=604800
```

### 1.4 Login Error Responses

| HTTP | Condition | Client Behavior |
|------|-----------|-----------------|
| `401` | Invalid email or password | Show generic error (do not reveal which field failed) |
| `423` | Account locked after 5 failures | Show lockout message with retry time |
| `403` | Tenant `suspended` or `cancelled` | Show billing/support contact message |
| `429` | Rate limit exceeded (IP) | Retry with backoff |

### 1.5 Post-Login Server Actions

| Action | Detail |
|--------|--------|
| Session record | New row in `core.user_sessions` with hashed refresh token |
| Audit | `audit.audit_logs` entry: `action=login`, `user_id`, `ip_address` |
| Tenant context | Subsequent requests use JWT `tenant_id` + `SET LOCAL app.tenant_id` |
| Permission cache | Warm Redis key `tenant:{id}:permissions:{user_id}` on first protected call |
| 2FA gate (Sprint 11+) | Owner/Admin may require TOTP step before issuing tokens |

---

## 2. JWT Access Token Flow

Access tokens are **short-lived, signed JWTs** used as `Authorization: Bearer` on every API call. They are intentionally minimal to reduce exposure and stale authorization data.

### 2.1 Token Specification

| Attribute | Value |
|-----------|-------|
| Format | JWT (RFC 7519) |
| Algorithm | **RS256** (asymmetric) |
| Signing key | Private key in AWS Secrets Manager |
| Verification key | Public key distributed to API instances |
| Issuer (`iss`) | `https://auth.platform.com` (tenant realm) or `platform-admin` (platform realm) |
| Lifetime | **30 minutes** |
| Storage (client) | **JavaScript memory only** — never `localStorage` or `sessionStorage` |

### 2.2 Access Token Payload (Authoritative)

```json
{
  "iss": "https://auth.platform.com",
  "sub": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "tenant_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "roles": ["doctor"],
  "iat": 1718611200,
  "exp": 1718613000,
  "jti": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
}
```

| Claim | Purpose |
|-------|---------|
| `sub` | Authenticated user UUID (`core.users.id`) |
| `tenant_id` | Tenant scope for all data access |
| `roles` | UI menu rendering and dashboard redirect only |
| `jti` | Unique token ID for revocation denylist |
| `exp` | Expiry — client must refresh before this time |

**Not included:** `permissions`, `email`, patient data, or subscription details.

### 2.3 Authenticated Request Flow

```mermaid
sequenceDiagram
    autonumber
    participant FE as React SPA
    participant API as FastAPI Middleware
    participant Redis as Redis
    participant DB as PostgreSQL

    FE->>API: GET /api/v1/patients<br/>Authorization: Bearer {access_token}

    API->>API: Verify RS256 signature + exp
    API->>Redis: Is jti in denylist?
    alt jti revoked
        API-->>FE: 401 Unauthorized
    end

    API->>API: Extract sub, tenant_id, roles from claims
    API->>DB: Verify tenant status (trial/active/past_due)
    alt tenant suspended
        API-->>FE: 403 tenant_suspended
    end

    API->>Redis: Get permissions cache<br/>tenant:{id}:permissions:{user_id}
    alt cache miss
        API->>DB: JOIN user_roles → role_permissions → permissions
        API->>Redis: SET cache TTL 5 min
    end

    API->>API: @requires_permission("patient:read")
    API->>DB: SET LOCAL app.tenant_id = '{tenant_id}'
    API->>DB: SELECT ... WHERE tenant_id = $1
    API-->>FE: 200 { data, meta, errors }
```

### 2.4 Example Authenticated API Call

```http
GET /api/v1/patients?page=1&page_size=20 HTTP/1.1
Host: apollo.platform.com
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
X-Request-ID: 7c9e6679-7425-40de-944b-e07fc1f90ae7
Accept: application/json
```

### 2.5 Access Token Revocation

Because JWTs are stateless, revocation before expiry uses a **Redis denylist** keyed by `jti`:

| Event | Action |
|-------|--------|
| Logout | Add `jti` to `jwt:denylist:{jti}` with TTL = remaining token life |
| Password change | Denylist all active access tokens for user (via session invalidation + short TTL) |
| Role change | Permissions cache invalidated; access token remains valid until expiry (max 30 min) |
| Admin deactivates user | Revoke all sessions; denylist active `jti` values |

**Design trade-off:** Up to 30 minutes of stale role permissions after role change — acceptable given short TTL. For immediate effect, force session revocation on role assignment (Sprint 2+).

### 2.6 Frontend Token Handling

| Rule | Rationale |
|------|-----------|
| Store access token in React state / closure | Prevents XSS exfiltration from persistent storage |
| Attach token via Axios interceptor | Centralized auth header injection |
| On 401 with valid refresh cookie | Call `POST /auth/refresh`, retry original request |
| On refresh failure | Clear state, redirect to `/login` |
| Never log token value | Log `jti` only in diagnostics |

---

## 3. Refresh Token Flow

Refresh tokens provide **long-lived session continuity** without keeping access tokens valid for extended periods. They are **opaque strings** (not JWTs) stored securely on the client.

### 3.1 Refresh Token Specification

| Attribute | Value |
|-----------|-------|
| Format | Cryptographically random opaque string (256+ bits) |
| Client storage | **HttpOnly, Secure, SameSite=Strict** cookie |
| Server storage | **SHA-256 hash** in `core.user_sessions.refresh_token_hash` |
| Lifetime | **7 days** (`expires_at`) |
| Rotation | **New refresh token on every refresh**; old token invalidated |
| Max concurrent sessions | **5 per user** (configurable) |

### 3.2 Refresh Sequence

```mermaid
sequenceDiagram
    autonumber
    participant FE as React SPA
    participant API as POST /api/v1/auth/refresh
    participant DB as PostgreSQL
    participant Redis as Redis

    FE->>API: API call with expired access token
    API-->>FE: 401 Unauthorized

    FE->>API: POST /auth/refresh<br/>Cookie: refresh_token=...
    API->>API: Validate Origin header (CSRF mitigation)
    API->>DB: Lookup session by refresh_token_hash
    Note over API,DB: WHERE hash = SHA256(token)<br/>AND revoked_at IS NULL<br/>AND expires_at > NOW()

    alt Session not found or revoked
        API-->>FE: 401 → redirect to login
    else Valid session
        API->>DB: Revoke old session (rotation)
        API->>API: Issue new access JWT (new jti)
        API->>API: Generate new refresh token
        API->>DB: INSERT new user_sessions row
        API-->>FE: 200 { access_token, expires_in }
        API-->>FE: Set-Cookie: new refresh_token
        FE->>API: Retry original request with new access_token
    end
```

### 3.3 Refresh Request Example

**Request (no body — cookie only):**

```http
POST /api/v1/auth/refresh HTTP/1.1
Host: apollo.platform.com
Cookie: refresh_token=s%3A8f3a2b1c...
Origin: https://apollo.platform.com
```

**Success response:**

```json
{
  "data": {
    "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800
  },
  "meta": {
    "request_id": "...",
    "timestamp": "2026-06-17T11:00:00Z"
  },
  "errors": null
}
```

### 3.4 Refresh Token Rotation (Security)

```mermaid
stateDiagram-v2
    [*] --> Active: Login issues Token A
    Active --> Rotated: Refresh with Token A
    Rotated --> Active: Issues Token B, revokes A
    Active --> Revoked: Logout / password change
    Rotated --> ReuseDetected: Token A used again
    ReuseDetected --> AllRevoked: Revoke all user sessions
    Revoked --> [*]
    AllRevoked --> [*]
```

**Reuse detection:** If a revoked refresh token is presented, treat as potential theft — revoke **all** sessions for that user and require re-login. Log security event at Warning severity.

### 3.5 Session Database Record

Each refresh maps to `core.user_sessions`:

| Column | Example | Purpose |
|--------|---------|---------|
| `tenant_id` | `7c9e6679-...` | Tenant scope |
| `user_id` | `a1b2c3d4-...` | Session owner |
| `refresh_token_hash` | `sha256(...)` | Never store plaintext token |
| `ip_address` | `203.0.113.42` | Session binding / audit |
| `user_agent` | `Mozilla/5.0...` | Device identification |
| `expires_at` | `2026-06-24T10:30:00Z` | 7-day expiry |
| `revoked_at` | `NULL` or timestamp | Logout / rotation |

---

## 4. Password Hashing Strategy

Passwords are **never stored in plaintext** and **never logged**. Only password hashes are persisted in `core.users.password_hash`.

### 4.1 Hashing Algorithm

| Priority | Algorithm | Parameters |
|----------|-----------|------------|
| **Primary (MVP)** | bcrypt | Cost factor **12** |
| **Alternative** | Argon2id | Memory 64 MB, iterations 3, parallelism 4 |

**Selection guidance:** Use bcrypt for MVP (widely supported). Migrate to Argon2id in Phase 2 if performance testing warrants it. Never use MD5, SHA-1, or plain SHA-256 for passwords.

### 4.2 Password Policy

| Rule | Requirement |
|------|-------------|
| Minimum length | 8 characters |
| Uppercase | At least 1 |
| Lowercase | At least 1 |
| Number | At least 1 |
| Special character | At least 1 |
| Maximum length | 128 characters (prevent DoS via long inputs) |
| Password history | Last 5 passwords cannot be reused (Phase 2) |
| Breach check | HaveIBeenPwned k-anonymity API on registration (Phase 2) |

**Example valid password:** `SecurePass@123`  
**Example rejected:** `password` (no uppercase, number, special char)

### 4.3 Hashing Lifecycle

```mermaid
flowchart LR
    REG["Registration /<br/>Reset /<br/>Invite accept"] --> VAL["Validate policy<br/>(Pydantic)"]
    VAL --> HASH["bcrypt.hash<br/>cost=12"]
    HASH --> STORE["Store in<br/>password_hash"]
    LOGIN["Login attempt"] --> COMPARE["bcrypt.verify<br/>(plain, hash)"]
    COMPARE -->|match| OK["Issue tokens"]
    COMPARE -->|fail| FAIL["Increment<br/>failed_login_attempts"]
```

### 4.4 Password Reset Token Storage

Password reset uses the same **hash-only** principle as refresh tokens:

| Store | Table | Field | TTL |
|-------|-------|-------|-----|
| Reset token hash | `core.password_reset_tokens` | `token_hash` | 1 hour |
| Single use | — | `used_at` set on consumption | — |

**Reset link format:**

```
https://apollo.platform.com/reset-password?token=<single-use-opaque-token>
```

On successful reset: update `password_hash`, set `used_at`, **revoke all `user_sessions`**, audit `action=password_reset`.

### 4.5 Forgot-Password Anti-Enumeration

`POST /auth/forgot-password` **always returns 200** with a generic message whether or not the email exists:

```json
{
  "data": {
    "message": "If the email exists, a reset link has been sent."
  }
}
```

This prevents attackers from discovering valid email addresses per tenant.

---

## 5. User Session Strategy

The platform uses a **hybrid session model**: stateless access (JWT) + stateful refresh (database sessions).

### 5.1 Session Model Overview

```mermaid
flowchart TB
    subgraph Stateless["Stateless Layer"]
        AT["Access JWT<br/>30 min · no DB lookup"]
    end

    subgraph Stateful["Stateful Layer"]
        RT["Refresh Token<br/>HttpOnly cookie"]
        US["core.user_sessions"]
        RD["Redis jti denylist"]
        PC["Redis permissions cache"]
    end

    AT -->|every API call| API["FastAPI"]
    RT -->|refresh only| API
    API --> US
    API --> RD
    API --> PC
```

| Component | Stateful? | Purpose |
|-----------|-------------|---------|
| Access JWT | No | Fast API authentication |
| Refresh token + `user_sessions` | Yes | Long-lived login, rotation, revocation |
| Redis `jti` denylist | Yes | Early access token invalidation |
| Redis permissions cache | Yes | Avoid DB permission lookup every request |

### 5.2 Concurrent Session Limits

| Rule | Value |
|------|-------|
| Max active sessions per user | 5 |
| On 6th login | Revoke oldest session (by `created_at`) |
| User-visible | "Active sessions" list in account settings (Phase 2) |

### 5.3 Session Invalidation Triggers

| Event | Sessions Affected | Access Token |
|-------|-------------------|--------------|
| Logout (current device) | Current session `revoked_at` set | `jti` denylisted |
| Logout all devices | All user sessions revoked | All active `jti` denylisted |
| Password reset | All sessions revoked | Denylist |
| Password change | All sessions revoked | Denylist |
| Admin deactivates user | All sessions revoked | Denylist |
| Account locked | No new logins; existing sessions may continue until refresh fails |
| Role permission change | Sessions remain; permission cache invalidated |

### 5.4 Session Binding (Optional Hardening)

| Binding | MVP | Phase 2 |
|---------|-----|---------|
| IP address stored in `user_sessions` | ✅ Audit only | Alert on change |
| User-Agent stored | ✅ Audit only | Alert on change |
| Device fingerprint | — | Optional strict binding |

### 5.5 `GET /auth/me` — Session Identity Endpoint

After login, the frontend calls `GET /auth/me` to hydrate user profile and permissions:

```json
{
  "data": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "email": "doctor@apollo.com",
    "first_name": "Vikram",
    "last_name": "Patel",
    "roles": ["doctor"],
    "permissions": [
      "patient:read",
      "patient:update",
      "opd:read",
      "opd:consult",
      "opd:prescribe"
    ],
    "tenant_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "staff_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "location_id": null
  }
}
```

Permissions here are for **UI rendering** (`<PermissionGuard>`). The API re-checks permissions independently.

---

## 6. Multi-Tenant Authentication

Authentication and tenancy are tightly coupled: a user belongs to **exactly one tenant**, and every token is **cryptographically bound** to that tenant.

### 6.1 Two Realms

| Realm | Issuer | Users | JWT `tenant_id` | Clinical Data |
|-------|--------|-------|-----------------|---------------|
| **Tenant** | `https://auth.platform.com` | Hospital staff | Required | Per RBAC |
| **Platform** | `platform-admin` | SaaS operators | Optional / N/A | **Denied by default** |

### 6.2 Tenant Resolution Timeline

```mermaid
flowchart TD
    subgraph Login["Unauthenticated (Login / Register)"]
        HOST["Host: apollo.platform.com"] --> SLUG["Extract subdomain 'apollo'"]
        SLUG --> LOOKUP["DB: platform.tenants"]
        LOOKUP --> TID["tenant_id resolved"]
    end

    subgraph Authenticated["Authenticated (All API calls)"]
        JWT["JWT tenant_id claim"] --> AUTH["Authoritative tenant context"]
        AUTH --> IGNORE["Ignore tenant_id in body/query/path"]
    end

    Login --> ISSUE["Issue JWT with tenant_id"]
    ISSUE --> Authenticated
```

| Phase | Tenant Source | Authority |
|-------|---------------|-----------|
| Login / register | Subdomain → DB lookup | Resolved then embedded in JWT |
| Authenticated API | JWT `tenant_id` claim | **Authoritative** |
| Background jobs | `tenant_id` in SQS message | Explicit per job |
| Platform admin | Explicit param + platform JWT | Audited; no clinical default |

### 6.3 Tenant + User Uniqueness

| Identifier | Scope | Example |
|------------|-------|---------|
| `email` (user) | Unique **per tenant** | `doctor@apollo.com` in Tenant A and Tenant B = two users |
| `slug` / `subdomain` | Unique **platform-wide** | `apollo` → one tenant |
| JWT `tenant_id` | Single value per token | Token for Tenant A cannot access Tenant B |

**Attack prevented:** User obtains patient UUID from Tenant A and calls API with Tenant B token → RLS + `tenant_id` filter returns **404** (not 403).

### 6.4 Subscription Status Gate (Post-Auth)

After JWT validation, middleware checks `platform.tenant_subscriptions.status`:

| Tenant Status | Login Allowed | API Access |
|---------------|---------------|------------|
| `trial` | ✅ | Full (within plan limits) |
| `active` | ✅ | Full |
| `past_due` | ✅ | Full (grace period) |
| `suspended` | ❌ or limited | **403** on mutations |
| `cancelled` | ❌ | Export window only |

### 6.5 Multi-Tenant Registration Flow

Self-service signup creates **tenant + admin user** in one transaction:

```mermaid
sequenceDiagram
    participant U as Hospital Owner
    participant API as POST /auth/register
    participant DB as PostgreSQL

    U->>API: org details + admin email + password
    Note over API: X-Idempotency-Key required
    API->>DB: platform.create_tenant()
    API->>DB: trial subscription (14 days)
    API->>DB: clone roles from system tenant
    API->>DB: create admin user (hospital_owner)
    API->>DB: assign user_roles
    API-->>U: 201 { tenant_id, trial_ends_at }
    Note over U: Email verification sent (async)
```

**Example registration payload** (from `API_DESIGN.md` §3.2):

```json
{
  "organization_name": "Apollo Clinic",
  "slug": "apollo-clinic",
  "admin_first_name": "Rajesh",
  "admin_last_name": "Kumar",
  "email": "admin@apollo.com",
  "phone": "9876543210",
  "password": "SecurePass@123",
  "plan_code": "starter",
  "country": "IN",
  "timezone": "Asia/Kolkata"
}
```

### 6.6 Staff Invite Flow (Tenant-Scoped)

Invited users are created **inactive** until they accept:

| Step | Endpoint | Result |
|------|----------|--------|
| Admin invites | `POST /api/v1/staff/users/invite` | User `status=inactive`, invite token emailed |
| User accepts | `POST /api/v1/auth/accept-invite` | Password set, `status=active`, tokens issued |

---

## 7. User Lifecycle

### 7.1 User Status State Machine

```mermaid
stateDiagram-v2
    [*] --> inactive: Staff invite created
    inactive --> active: Accept invite / email verified
    active --> locked: 5 failed login attempts
    locked --> active: locked_until expires OR admin unlock
    active --> inactive: Admin deactivates
    inactive --> active: Admin reactivates
    active --> [*]: Soft delete (admin)
```

| Status | DB Value | Can Login? | Description |
|--------|----------|------------|-------------|
| Inactive | `inactive` | ❌ | Invited but not yet activated |
| Active | `active` | ✅ | Normal operation |
| Locked | `locked` | ❌ | Temporary lockout (`locked_until` set) |

### 7.2 Lifecycle Events

| Event | Trigger | Auth Impact |
|-------|---------|-------------|
| **Registration** | `POST /auth/register` | Creates `hospital_owner` user + tenant |
| **Email verification** | Click link in email | Sets `email_verified_at`; may gate features |
| **Staff invite** | Admin invites user | `inactive` user + invite token |
| **Invite accept** | `POST /auth/accept-invite` | Password set → `active` → login tokens |
| **Login** | `POST /auth/login` | Session created; `last_login_at` updated |
| **Failed login** | Wrong password | `failed_login_attempts++`; lock at 5 |
| **Password reset** | Forgot password flow | All sessions revoked |
| **Role change** | Admin patches `user_roles` | Permission cache invalidated |
| **Deactivation** | `POST .../deactivate` | `status=inactive`; all sessions revoked |
| **Reactivation** | Admin patches user | `status=active`; user must login again |
| **Tenant cancellation** | Subscription cancelled | Login blocked after export window |

### 7.3 Account Lockout Detail

| Parameter | Value |
|-----------|-------|
| Threshold | 5 consecutive failed logins |
| Lock duration | **15 minutes** (`locked_until`) |
| Counter reset | On successful login |
| IP rate limit | 10 login attempts per minute per IP |
| Audit | Each failure logged; lockout triggers email to user |

### 7.4 Email Verification

| State | `email_verified_at` | Access |
|-------|---------------------|--------|
| Unverified | `NULL` | Limited trial features until verified |
| Verified | Timestamp set | Full trial access |

Verification link:

```
https://apollo.platform.com/verify-email?token=<opaque-token>
```

### 7.5 User Lifecycle Data Model

Key `core.users` fields for authentication:

| Field | Purpose |
|-------|---------|
| `email` | Login identifier (unique per tenant) |
| `password_hash` | bcrypt/Argon2 hash |
| `status` | `active` / `inactive` / `locked` |
| `failed_login_attempts` | Brute-force counter |
| `locked_until` | Lockout expiry |
| `email_verified_at` | Verification timestamp |
| `last_login_at` | Security audit / anomaly detection |
| `tenant_id` | Tenant binding (immutable after create) |

---

## 8. Security Best Practices

### 8.1 Transport & Edge Security

| Control | Implementation |
|---------|----------------|
| TLS | TLS 1.2+ on all endpoints; HSTS enabled |
| WAF | AWS WAF — OWASP rules, geo blocking (optional) |
| Rate limiting | 10 req/min/IP on auth endpoints; 1,000 req/min/tenant on API |
| Security headers | `X-Content-Type-Options`, `X-Frame-Options`, CSP |

### 8.2 Token Security Summary

| Token | Do | Don't |
|-------|-----|-------|
| Access JWT | Keep in memory; short TTL; RS256 | Store in localStorage; put permissions in payload |
| Refresh token | HttpOnly cookie; rotate on use; hash server-side | Send in URL; store in JS; log value |
| Reset/invite tokens | Single-use; 1-hour TTL; hash server-side | Reuse tokens; long TTL |

### 8.3 CSRF Posture

| Endpoint | CSRF Risk | Mitigation |
|----------|-----------|------------|
| API calls with Bearer token | None | Token in header, not cookie |
| `POST /auth/refresh` | Low | `SameSite=Strict` + `Origin` header validation |
| Future cookie-auth | High | Not planned for MVP |

### 8.4 XSS Mitigation

| Vector | Mitigation |
|--------|------------|
| Stolen access token | Memory-only storage; 30-min TTL; CSP headers |
| Stolen refresh token | HttpOnly cookie not accessible to JS |
| Injected scripts | React escaping; CSP `script-src` restrictions |

### 8.5 Authentication Audit Events

| Event | `audit.audit_logs.action` | Alert |
|-------|---------------------------|-------|
| Successful login | `login` | — |
| Failed login | `login_failed` | Email after 5 failures |
| Logout | `logout` | — |
| Password reset | `password_reset` | Email to user |
| Permission denied | `access_denied` | Repeated → security review |
| Session revoked (reuse) | `session_reuse_detected` | Warning |
| Break-glass impersonation | `impersonate_start` | Email to tenant owner |

### 8.6 Secrets Management

| Secret | Storage | Never |
|--------|---------|-------|
| JWT private key | AWS Secrets Manager | In git, Docker image, or client |
| Database password | Secrets Manager | Hardcoded in app |
| Refresh token plaintext | Client cookie only (opaque) | In database or logs |
| Password plaintext | — | Stored or logged anywhere |

### 8.7 Two-Factor Authentication (Sprint 11+)

| Attribute | Value |
|-----------|-------|
| Method | TOTP (RFC 6238) |
| Required for | `hospital_owner`, `hospital_admin` |
| Recovery | 10 hashed backup codes (shown once) |
| Sensitive gates | `admin:subscription`, data export, `billing:void` (if 2FA enabled) |

### 8.8 Platform Admin & Break-Glass

Platform operators use a **separate auth realm** with stricter controls:

| Control | Detail |
|---------|--------|
| MFA | Mandatory TOTP for all platform admins |
| Clinical access | Denied by default |
| Impersonation | Max 15 min read-only; tenant email notification |
| Audit | Every action tagged `impersonated_by` |

```mermaid
sequenceDiagram
    participant PA as Platform Admin
    participant API as Platform API
    participant Owner as Hospital Owner

    PA->>API: POST /platform/support/break-glass
    Note over PA,API: tenant_id, reason, ticket_id
    API->>Owner: Email: support session starting
    API-->>PA: 15-min impersonation token (read_only)
    PA->>API: Tenant API calls (audited)
    Note over API: Token expires automatically
    API->>Owner: Email: support session ended
```

### 8.9 Compliance Considerations (Healthcare SaaS)

| Requirement | Auth Mechanism |
|-------------|----------------|
| Accountability | Audit logs for login, PHI access, permission denials |
| Least privilege | RBAC + server-side permission resolution |
| Session timeout | 30-min access TTL; 7-day refresh max |
| Breach containment | Session revocation, denylist, lockout |
| Data residency | Auth in `ap-south-1` (Mumbai) for MVP |

---

## 9. Logout Flow

Logout must invalidate **both** the access token (immediate) and refresh token (persistent session).

### 9.1 Logout Sequence

```mermaid
sequenceDiagram
    autonumber
    participant FE as React SPA
    participant API as POST /api/v1/auth/logout
    participant DB as PostgreSQL
    participant Redis as Redis

    FE->>API: POST /auth/logout<br/>Authorization: Bearer {access_token}<br/>Cookie: refresh_token

    API->>API: Validate access JWT; extract jti, user_id
    API->>Redis: SET jwt:denylist:{jti} TTL=remaining_exp
    API->>DB: UPDATE user_sessions SET revoked_at = NOW()<br/>WHERE refresh_token_hash matches
    API->>DB: audit_log(action=logout)
    API-->>FE: 204 No Content
    API-->>FE: Set-Cookie: refresh_token=; Max-Age=0
    FE->>FE: Clear access token from memory
    FE->>FE: Redirect to /login
```

### 9.2 Logout Request Example

```http
POST /api/v1/auth/logout HTTP/1.1
Host: apollo.platform.com
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Cookie: refresh_token=s%3A8f3a2b1c...
```

**Response:** `204 No Content` with expired cookie:

```http
Set-Cookie: refresh_token=; HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth; Max-Age=0
```

### 9.3 Logout Variants

| Variant | Scope | Implementation |
|---------|-------|----------------|
| **Current device** | This session only | Revoke matching `user_sessions` row |
| **All devices** | All user sessions | Revoke all rows for `user_id` + denylist all `jti` (Phase 2 UI) |
| **Admin force logout** | Target user | Admin API revokes all sessions for staff member |
| **Password change** | All devices | Automatic full revocation |

### 9.4 Client-Side Logout Checklist

| Step | Action |
|------|--------|
| 1 | Call `POST /auth/logout` with Bearer token |
| 2 | Clear in-memory access token |
| 3 | Clear TanStack Query cache (user-specific data) |
| 4 | Clear auth context state |
| 5 | Redirect to `/login` |
| 6 | Do not rely on client-only logout (server must revoke refresh token) |

---

## 10. Future SSO Support

Enterprise hospitals will require **Single Sign-On** via identity providers (Azure AD, Okta, Google Workspace). SSO is **post-MVP** (Phase 2+) but the current architecture is designed to accommodate it without breaking tenant isolation.

### 10.1 Planned Protocols

| Protocol | Priority | Use Case |
|----------|----------|----------|
| **SAML 2.0** | P1 (Enterprise) | Large hospital IT departments |
| **OpenID Connect (OIDC)** | P1 | Modern IdPs (Azure AD, Okta, Google) |
| **SCIM 2.0** | P2 | Automated user provisioning / deprovisioning |

Referenced in `RBAC_DESIGN.md` §11 and `ADVANCED_FEATURES_ROADMAP.md` (custom domain + SSO).

### 10.2 Target SSO Architecture

```mermaid
flowchart TB
    subgraph Tenant["Tenant: Apollo Clinic"]
        USER["Staff User"]
        IDP["Hospital IdP<br/>Azure AD / Okta"]
    end

    subgraph Platform["HMS SaaS"]
        SP["SAML SP / OIDC RP"]
        AUTH["Auth Service"]
        MAP["IdP Role Mapper"]
        DB[("core.users")]
    end

    USER --> IDP
    IDP -->|SAML Assertion / OIDC token| SP
    SP --> AUTH
    AUTH --> MAP
    MAP -->|JIT provision or match| DB
    AUTH -->|Issue HMS JWT| USER
```

### 10.3 SSO Design Principles (Future)

| Principle | Description |
|-----------|-------------|
| **Tenant-scoped IdP** | Each tenant configures their own IdP metadata (Enterprise plan) |
| **JIT provisioning** | First SSO login creates `core.users` row with mapped roles |
| **No shared passwords** | SSO users have `password_hash = NULL` or unusable placeholder |
| **Fallback** | `hospital_owner` retains local password for break-glass |
| **Same JWT format** | After SSO, issue identical HMS access + refresh tokens |
| **SCIM sync** | IdP group → `core.roles` mapping; deprovision revokes sessions |

### 10.4 SSO + Multi-Tenancy

| Challenge | Solution |
|-----------|----------|
| Same email in multiple tenants | IdP login includes tenant context via subdomain or `tenant_id` in SAML `RelayState` |
| Wrong tenant SSO | Subdomain `apollo.platform.com` → only Apollo's IdP config loaded |
| Role mapping | IdP groups mapped to `hospital_admin`, `doctor`, etc. per tenant config table |
| Session coexistence | HMS refresh token model unchanged; SSO is login method only |

### 10.5 Example OIDC Login Flow (Future)

```mermaid
sequenceDiagram
    participant U as User
    participant FE as React SPA
    participant API as HMS Auth
    participant IdP as Azure AD

    U->>FE: Click "Sign in with Microsoft"
    FE->>API: GET /auth/oidc/authorize?tenant=apollo
    API-->>FE: Redirect to Azure AD
    FE->>IdP: OIDC authorization request
    IdP-->>FE: Authorization code
    FE->>API: POST /auth/oidc/callback { code }
    API->>IdP: Exchange code for IdP tokens
    API->>API: Validate IdP token; map groups → roles
    API->>API: JIT create/update user
    API-->>FE: HMS access_token + refresh cookie
```

### 10.6 Custom Domain + SSO (Enterprise)

`ADVANCED_FEATURES_ROADMAP.md` envisions:

| Feature | Example |
|---------|---------|
| Custom domain | `hms.apollohospital.com` instead of `apollo.platform.com` |
| Wildcard SSL | Per-tenant certificate via ACM |
| IdP federation | SAML metadata per custom domain |

### 10.7 What to Build Now to Enable SSO Later

| MVP Implementation | SSO Extension Point |
|--------------------|---------------------|
| `core.users` with `email`, `tenant_id` | Add `idp_subject`, `idp_provider`, `auth_method` columns |
| JWT with `sub` + `tenant_id` | Unchanged after SSO |
| `user_sessions` refresh model | Unchanged after SSO |
| Role assignment via `user_roles` | SCIM / IdP group mapper writes same table |
| Separate platform admin realm | Remains separate from tenant SSO |

### 10.8 SSO Roadmap Phases

| Phase | Capability | Timeline |
|-------|------------|----------|
| MVP | Email + password only | Sprints 2–12 |
| Phase 2 | OIDC (Azure AD, Google) for Enterprise tier | Post-launch |
| Phase 3 | SAML 2.0 + custom domain | Enterprise |
| Phase 4 | SCIM provisioning + automated deprovisioning | Enterprise |

---

## Appendix A — Auth API Endpoint Reference

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | `/api/v1/auth/register` | Public | Tenant + owner signup |
| POST | `/api/v1/auth/login` | Public | Email/password login |
| POST | `/api/v1/auth/refresh` | Cookie | Renew access token |
| POST | `/api/v1/auth/logout` | Bearer | End session |
| POST | `/api/v1/auth/forgot-password` | Public | Request reset email |
| POST | `/api/v1/auth/reset-password` | Public | Consume reset token |
| POST | `/api/v1/auth/accept-invite` | Public | Activate invited user |
| GET | `/api/v1/auth/me` | Bearer | Current user + permissions |

Full request/response schemas: `API_DESIGN.md` §3.

---

## Appendix B — Database Tables (Auth)

| Table | Schema | Purpose |
|-------|--------|---------|
| `users` | `core` | Credentials, status, lockout counters |
| `user_sessions` | `core` | Refresh token hashes, session metadata |
| `password_reset_tokens` | `core` | Hashed reset tokens |
| `roles` | `core` | Tenant-scoped roles |
| `permissions` | `core` | Permission catalog |
| `user_roles` | `core` | User ↔ role mapping |
| `role_permissions` | `core` | Role ↔ permission mapping |
| `audit_logs` | `audit` | Login, logout, security events |
| `tenants` | `platform` | Tenant root for isolation |

---

## Appendix C — Implementation Sprint Mapping

| Capability | Sprint | Reference |
|------------|--------|-----------|
| Auth endpoints + JWT RS256 | Sprint 2 | `IMPLEMENTATION_PLAN.md` §2.1 |
| Permission resolver + `@requires_permission` | Sprint 2 | `RBAC_DESIGN.md` §7 |
| Registration + trial subscription | Sprint 2 | `MULTI_TENANT_DESIGN.md` §3 |
| Staff invite + accept-invite | Sprint 3 | `API_DESIGN.md` §11 |
| TOTP 2FA | Sprint 11 | `SECURITY_ARCHITECTURE.md` §5.6 |
| SSO / SAML / OIDC | Post-MVP | This document §10 |

---

## Appendix D — Document Errata

When implementing authentication, prefer this guide and `SECURITY_ARCHITECTURE.md` over older examples:

| Topic | Outdated Reference | Correct Approach |
|-------|-------------------|------------------|
| Permissions in JWT | `SYSTEM_ARCHITECTURE.md` §6.3 example payload | Server-side resolution; roles only in JWT |
| Lockout duration | `SYSTEM_ARCHITECTURE.md` (30 min) | **15 minutes** per `SECURITY_ARCHITECTURE.md` §5.5 |
| Role names in examples | `tenant_admin`, `billing_staff` | `hospital_owner`, `accountant` per `RBAC_DESIGN.md` |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | June 2026 | Security Architecture | Initial authentication architecture guide |

---

*This document is the engineering reference for Sprint 2 authentication implementation. For authorization (RBAC permission matrices), see `RBAC_DESIGN.md`. For tenant isolation beyond auth, see `MULTI_TENANT_DESIGN.md`.*
