# Non-Functional Requirements Document (NFRD)

## Multi-Tenant Hospital Management SaaS Platform

| Field | Value |
|-------|-------|
| **Document Version** | 1.0 |
| **Status** | Draft |
| **Last Updated** | June 2026 |
| **Tech Stack** | React.js, TypeScript, TailwindCSS · Python, FastAPI · SQL Database |
| **Related Documents** | PRD.md, SECURITY_ARCHITECTURE.md, SYSTEM_ARCHITECTURE.md, DEPLOYMENT_GUIDE.md |

---

## 1. Introduction

### 1.1 Purpose

This document defines the **non-functional requirements (NFRs)** for the Multi-Tenant Hospital Management SaaS Platform. NFRs specify quality attributes, constraints, and operational characteristics that the system must exhibit beyond functional behavior.

### 1.2 NFR ID Convention

```
NFR-<CATEGORY>-<NUMBER>

Categories: PERF (Performance), SCAL (Scalability), AVAIL (Availability),
            SEC (Security), COMP (Compliance), USAB (Usability), MAINT (Maintainability),
            COMPAT (Compatibility), DATA (Data Management), OPS (Operations)
```

---

## 2. Performance Requirements

| ID | Requirement | Target | Measurement Method |
|----|-------------|--------|-------------------|
| NFR-PERF-001 | API response time (P50) | < 200ms | Application Performance Monitoring (APM) |
| NFR-PERF-002 | API response time (P95) | < 500ms | APM |
| NFR-PERF-003 | API response time (P99) | < 1000ms | APM |
| NFR-PERF-004 | Page initial load time | < 3 seconds | Real User Monitoring (RUM) |
| NFR-PERF-005 | Page navigation (SPA route change) | < 1 second | RUM |
| NFR-PERF-006 | Patient search response time | < 1 second for 100,000 records | Load test |
| NFR-PERF-007 | Report generation (standard reports) | < 10 seconds | Load test |
| NFR-PERF-008 | PDF generation (invoice, lab report) | < 5 seconds | Load test |
| NFR-PERF-009 | Database query execution (single-tenant scoped) | < 100ms for indexed queries | Query profiling |
| NFR-PERF-010 | Concurrent API requests per tenant | 100 concurrent without degradation | Load test |
| NFR-PERF-011 | File upload (documents, images) | < 10 seconds for 5MB file | Manual test |
| NFR-PERF-012 | Real-time queue update latency | < 2 seconds | WebSocket/polling measurement |

### 2.1 Performance Under Load

| Scenario | Users | Expected Response (P95) |
|----------|-------|------------------------|
| Normal operations | 50 concurrent users/tenant | < 500ms |
| Peak hours (morning OPD rush) | 200 concurrent users/platform | < 800ms |
| Report generation (batch) | 10 concurrent reports | < 15 seconds |
| Tenant onboarding | 5 simultaneous signups | < 3 seconds per signup |

---

## 3. Scalability Requirements

| ID | Requirement | Target | Notes |
|----|-------------|--------|-------|
| NFR-SCAL-001 | Support total tenants on platform | 500 tenants (Year 1) | Horizontal scaling of app servers |
| NFR-SCAL-002 | Support tenants on platform (Year 3) | 5,000 tenants | Database read replicas, connection pooling |
| NFR-SCAL-003 | Patients per tenant | Up to 500,000 records | Indexed `tenant_id` + search columns |
| NFR-SCAL-004 | Concurrent users per tenant | Up to 200 | Connection pooling, caching |
| NFR-SCAL-005 | Total platform concurrent users | Up to 10,000 | Auto-scaling application tier |
| NFR-SCAL-006 | Database storage per tenant | Up to 50 GB | Partitioning strategy for large tenants |
| NFR-SCAL-007 | API throughput | 5,000 requests/second (platform) | Load balancer + multiple app instances |
| NFR-SCAL-008 | File storage per tenant | Up to 100 GB | Object storage (S3-compatible) |
| NFR-SCAL-009 | Horizontal scaling | Application tier scales independently | Containerized deployment (Kubernetes/Docker) |
| NFR-SCAL-010 | Database scaling | Read replicas for reporting queries | Primary for writes, replicas for reads |

### 3.1 Multi-Tenant Scaling Strategy

```
                    ┌─────────────────┐
                    │  Load Balancer  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ FastAPI  │  │ FastAPI  │  │ FastAPI  │
        │ Instance │  │ Instance │  │ Instance │
        └────┬─────┘  └────┬─────┘  └────┬─────┘
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                    ┌───────────────┐
                    │   SQL DB      │
                    │  (Primary)    │
                    └───────┬───────┘
                            │
                    ┌───────┴───────┐
                    ▼               ▼
              ┌──────────┐   ┌──────────┐
              │ Read     │   │ Read     │
              │ Replica  │   │ Replica  │
              └──────────┘   └──────────┘
```

---

## 4. Availability & Reliability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-AVAIL-001 | Platform uptime (monthly) | 99.9% (≤ 43 minutes downtime/month) |
| NFR-AVAIL-002 | Planned maintenance window | Max 4 hours/month, scheduled off-peak |
| NFR-AVAIL-003 | Maintenance notification lead time | 48 hours advance notice |
| NFR-AVAIL-004 | Mean Time Between Failures (MTBF) | > 720 hours |
| NFR-AVAIL-005 | Mean Time to Recovery (MTTR) | < 1 hour |
| NFR-AVAIL-006 | Recovery Point Objective (RPO) | < 1 hour (max data loss) |
| NFR-AVAIL-007 | Recovery Time Objective (RTO) | < 4 hours (max downtime) |
| NFR-AVAIL-008 | Database backup frequency | Every 6 hours (automated) |
| NFR-AVAIL-009 | Backup retention period | 30 days (daily), 12 months (monthly) |
| NFR-AVAIL-010 | Disaster recovery site | Secondary region with failover capability |
| NFR-AVAIL-011 | Health check endpoint | `/health` returns status within 1 second |
| NFR-AVAIL-012 | Graceful degradation | Non-critical features fail without affecting core workflows |

---

## 5. Security Requirements

| ID | Requirement | Implementation |
|----|-------------|----------------|
| NFR-SEC-001 | All data in transit encrypted via TLS 1.2+ | HTTPS enforced; HSTS enabled |
| NFR-SEC-002 | All data at rest encrypted | AES-256 encryption on database and file storage |
| NFR-SEC-003 | Tenant data isolation enforced at application layer | Middleware injects `tenant_id`; query filters mandatory |
| NFR-SEC-004 | Tenant data isolation enforced at database layer | Row-Level Security (RLS) policies where supported |
| NFR-SEC-005 | Authentication via JWT with short-lived access tokens | Access token: 30 min; Refresh token: 7 days |
| NFR-SEC-006 | Password storage using bcrypt/argon2 hashing | No plaintext passwords stored |
| NFR-SEC-007 | SQL injection prevention | Parameterized queries / ORM exclusively |
| NFR-SEC-008 | XSS prevention | Input sanitization; Content Security Policy headers |
| NFR-SEC-009 | CSRF protection | CSRF tokens on state-changing requests |
| NFR-SEC-010 | Rate limiting on authentication endpoints | Max 10 login attempts/minute/IP |
| NFR-SEC-011 | API rate limiting per tenant | 1,000 requests/minute/tenant |
| NFR-SEC-012 | Security headers (X-Frame-Options, X-Content-Type-Options, etc.) | Configured on all responses |
| NFR-SEC-013 | Dependency vulnerability scanning | Automated scanning in CI/CD pipeline |
| NFR-SEC-014 | Penetration testing | Annual third-party pen test |
| NFR-SEC-015 | Secrets management | Environment variables / secrets manager (no hardcoded secrets) |
| NFR-SEC-016 | Audit logging of security events | Login failures, permission denials, data exports logged |
| NFR-SEC-017 | Session invalidation on password change | All active sessions terminated |
| NFR-SEC-018 | IP allowlisting (Enterprise tier) | Configurable per tenant |
| NFR-SEC-019 | Two-factor authentication (2FA) | TOTP-based 2FA (Phase 2) |
| NFR-SEC-020 | Zero cross-tenant data leakage | Verified by automated isolation tests in CI |

---

## 6. Compliance Requirements

| ID | Requirement | Standard/Regulation |
|----|-------------|---------------------|
| NFR-COMP-001 | Patient data privacy and protection | DPDP Act 2023 (India), applicable local laws |
| NFR-COMP-002 | Health data security practices | ISO 27001 aligned practices |
| NFR-COMP-003 | Audit trail for all data modifications | 7-year retention minimum |
| NFR-COMP-004 | Patient consent management | Record consent with timestamp and method |
| NFR-COMP-005 | Right to data portability | Tenant data export in machine-readable format |
| NFR-COMP-006 | Right to erasure (where applicable) | Patient data anonymization/deletion workflow |
| NFR-COMP-007 | Data residency | Data stored in tenant's selected region (Phase 2) |
| NFR-COMP-008 | Terms of Service and Privacy Policy | Accepted during signup; versioned |
| NFR-COMP-009 | Medical record retention | Configurable; minimum 7 years default |
| NFR-COMP-010 | Access logging for sensitive data | Who accessed which patient record, when |

---

## 7. Usability Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-USAB-001 | New user onboarding (receptionist role) | Productive within 30 minutes of training |
| NFR-USAB-002 | Patient registration workflow | Completable in < 2 minutes |
| NFR-USAB-003 | OPD consultation workflow (doctor) | Patient history accessible within 2 clicks |
| NFR-USAB-004 | System Learnability (SUS Score) | ≥ 70 (System Usability Scale) |
| NFR-USAB-005 | Error messages | Clear, actionable, non-technical language |
| NFR-USAB-006 | Form validation | Inline validation with immediate feedback |
| NFR-USAB-007 | Responsive design | Functional on screens ≥ 1024px (desktop primary); usable on tablets (768px+) |
| NFR-USAB-008 | Keyboard navigation | Core workflows navigable via keyboard |
| NFR-USAB-009 | Color contrast | WCAG 2.1 AA compliance |
| NFR-USAB-010 | Loading indicators | Visible for operations > 1 second |
| NFR-USAB-011 | Confirmation dialogs | Destructive actions require confirmation |
| NFR-USAB-012 | Contextual help | Tooltips and help links on complex forms |
| NFR-USAB-013 | Consistent UI patterns | Shared design system (TailwindCSS components) |
| NFR-USAB-014 | Language support | English (MVP); Hindi (Phase 2) |

---

## 8. Maintainability Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-MAINT-001 | Code coverage (unit tests) | ≥ 80% for backend business logic |
| NFR-MAINT-002 | Code coverage (integration tests) | ≥ 60% for API endpoints |
| NFR-MAINT-003 | Code documentation | All public API endpoints documented (OpenAPI/Swagger) |
| NFR-MAINT-004 | Database migration strategy | Versioned migrations; rollback capability |
| NFR-MAINT-005 | Deployment frequency | Weekly releases (non-breaking); daily (hotfixes) |
| NFR-MAINT-006 | Zero-downtime deployments | Blue-green or rolling deployment strategy |
| NFR-MAINT-007 | Feature flags | New features deployable behind flags |
| NFR-MAINT-008 | Logging | Structured JSON logging with correlation IDs |
| NFR-MAINT-009 | Monitoring and alerting | Dashboards for CPU, memory, DB connections, error rates |
| NFR-MAINT-010 | Error tracking | Centralized error tracking (e.g., Sentry) |
| NFR-MAINT-011 | Code style enforcement | Linting (ESLint, Ruff/Flake8) in CI pipeline |
| NFR-MAINT-012 | Architecture documentation | Updated with each major release |

---

## 9. Compatibility Requirements

| ID | Requirement | Details |
|----|-------------|---------|
| NFR-COMPAT-001 | Browser support (desktop) | Chrome 90+, Firefox 90+, Edge 90+, Safari 15+ |
| NFR-COMPAT-002 | Browser support (tablet) | Chrome, Safari on iPad (768px+) |
| NFR-COMPAT-003 | Screen resolution (minimum) | 1024 × 768 (desktop primary) |
| NFR-COMPAT-004 | API versioning | URL-based versioning (`/api/v1/`) |
| NFR-COMPAT-005 | Backward compatibility | API v1 supported for minimum 12 months after v2 release |
| NFR-COMPAT-006 | Database compatibility | PostgreSQL 14+ (primary); MySQL 8+ (alternative) |
| NFR-COMPAT-007 | Export format compatibility | CSV (UTF-8), PDF (PDF/A), JSON |
| NFR-COMPAT-008 | Payment gateway | Razorpay, Stripe (region-dependent) |
| NFR-COMPAT-009 | SMS gateway | Twilio, MSG91 (region-dependent) |
| NFR-COMPAT-010 | Email delivery | SMTP, SendGrid, AWS SES |

---

## 10. Data Management Requirements

| ID | Requirement | Details |
|----|-------------|---------|
| NFR-DATA-001 | Data model versioning | Schema changes via versioned migrations only |
| NFR-DATA-002 | Tenant data export | Full export within 24 hours of request |
| NFR-DATA-003 | Tenant data deletion | Complete deletion within 30 days of request (post-retention) |
| NFR-DATA-004 | Data integrity | Foreign key constraints; referential integrity enforced |
| NFR-DATA-005 | Soft delete | Patient and critical records soft-deleted (not hard-deleted) |
| NFR-DATA-006 | Data archival | Records older than retention period archived, not deleted |
| NFR-DATA-007 | Database indexing | All `tenant_id` columns indexed; frequently queried columns indexed |
| NFR-DATA-008 | Connection pooling | PgBouncer or equivalent; max 100 connections per app instance |
| NFR-DATA-009 | Query optimization | No full table scans on tenant-scoped queries > 10,000 rows |
| NFR-DATA-010 | File storage | Object storage with tenant-prefixed paths (`/tenants/{tenant_id}/`) |
| NFR-DATA-011 | Data validation | Server-side validation on all inputs (Pydantic models) |
| NFR-DATA-012 | Clock synchronization | UTC timestamps throughout; display in tenant timezone |

---

## 11. Operational Requirements

| ID | Requirement | Details |
|----|-------------|---------|
| NFR-OPS-001 | CI/CD pipeline | Automated build, test, deploy on merge to main |
| NFR-OPS-002 | Environment separation | Development, Staging, Production environments |
| NFR-OPS-003 | Infrastructure as Code | Terraform/Pulumi for reproducible infrastructure |
| NFR-OPS-004 | Container orchestration | Docker containers; Kubernetes or managed container service |
| NFR-OPS-005 | Secret rotation | Database credentials rotated quarterly |
| NFR-OPS-006 | Log retention | Application logs retained for 90 days |
| NFR-OPS-007 | Audit log retention | Audit logs retained for 7 years |
| NFR-OPS-008 | Incident response | Documented runbook; on-call rotation |
| NFR-OPS-009 | Capacity planning review | Quarterly review of resource utilization |
| NFR-OPS-010 | Tenant provisioning automation | New tenant provisioned in < 5 minutes (automated) |
| NFR-OPS-011 | SSL certificate management | Auto-renewal via Let's Encrypt or managed certificates |
| NFR-OPS-012 | Database maintenance | Vacuum/analyze scheduled; index maintenance monthly |

---

## 12. Multi-Tenancy Specific NFRs

| ID | Requirement | Details |
|----|-------------|---------|
| NFR-MT-001 | Tenant context resolution | `tenant_id` resolved from JWT token on every request |
| NFR-MT-002 | Noisy neighbor isolation | Per-tenant rate limiting; query timeout enforcement |
| NFR-MT-003 | Tenant-specific configuration caching | Config cached per tenant; invalidated on change |
| NFR-MT-004 | Cross-tenant query prevention | Automated tests verify zero cross-tenant data in responses |
| NFR-MT-005 | Tenant resource quotas | Storage, API calls, users enforced per plan |
| NFR-MT-006 | Tenant onboarding isolation | New tenant setup does not impact existing tenants |
| NFR-MT-007 | Shared database performance | Composite indexes on (`tenant_id`, frequently queried columns) |
| NFR-MT-008 | Tenant offboarding | Data export + deletion within SLA; no residual data |

---

## 13. Risk Matrix (NFR-Related)

| Risk | Impact | Probability | NFR Mitigation |
|------|--------|-------------|----------------|
| Cross-tenant data leak | Critical | Low | NFR-SEC-003, NFR-SEC-004, NFR-SEC-020, NFR-MT-004 |
| Performance degradation at scale | High | Medium | NFR-PERF-*, NFR-SCAL-*, NFR-MT-007 |
| Data loss | Critical | Low | NFR-AVAIL-006, NFR-AVAIL-008, NFR-AVAIL-009 |
| Security breach | Critical | Low | NFR-SEC-*, NFR-COMP-* |
| Extended downtime | High | Low | NFR-AVAIL-*, NFR-OPS-008 |
| Compliance violation | Critical | Medium | NFR-COMP-*, NFR-SEC-016 |
| Poor user adoption | High | Medium | NFR-USAB-* |

---

## 14. NFR Verification & Testing Strategy

| Category | Verification Method | Frequency |
|----------|-------------------|-----------|
| Performance | Load testing (k6, Locust) | Per release |
| Scalability | Stress testing, capacity testing | Quarterly |
| Availability | Uptime monitoring, failover drills | Continuous / Quarterly |
| Security | SAST, DAST, pen testing, tenant isolation tests | Per release / Annual |
| Compliance | Audit log review, data export tests | Quarterly |
| Usability | User testing, SUS surveys | Per major release |
| Maintainability | Code coverage reports, CI pipeline metrics | Per commit |

---

## 15. Service Level Objectives (SLOs)

| SLO | Target | Measurement Window |
|-----|--------|-------------------|
| API Availability | 99.9% | Rolling 30 days |
| API Latency (P95) | < 500ms | Rolling 7 days |
| Error Rate | < 0.1% of requests | Rolling 7 days |
| Deployment Success Rate | > 99% | Rolling 30 days |
| Backup Success Rate | 100% | Rolling 30 days |
| Support Response (P1) | < 1 hour | Per incident |
| Support Resolution (P1) | < 4 hours | Per incident |

---

## 16. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | June 2026 | Product Team | Initial NFRD |
