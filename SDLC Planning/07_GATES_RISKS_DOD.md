# Gates, Risks & Definition of Done

---

## Decision Gates

| Gate | When | Go Criteria | No-Go Action |
|------|------|-------------|--------------|
| **G1 — Start feature work** | End Sprint 2 | Docker; CI; RLS framework; seeds; isolation tests; register API | Fix S2 blockers |

### Gate G1 Detailed Checklist (Sprint 2 — verified MVP-020)

- [x] Docker Compose (`docker-compose.yml`) runs PostgreSQL + Redis
- [x] GitHub Actions CI (lint + tests + isolation regression)
- [x] Alembic head `011_system_tenant_plans_seed` applied
- [x] Platform tables: `tenants`, `subscription_plans`, `tenant_subscriptions`, `tenant_locations`, `tenant_settings`
- [x] FORCE RLS on all platform tenant-scoped tables
- [x] `platform.create_tenant()` and `lookup_tenant_for_login()` deployed
- [x] `hms_app` database role for RLS enforcement
- [x] `TenantScopedRepository` + `SET app.tenant_id` session binding
- [x] System tenant + 3 subscription plans seeded (idempotent)
- [x] `POST /api/v1/platform/register` returns `201` with tenant id
- [x] CF-01 cross-tenant isolation regression (`test_tenant_isolation.py`)
- [x] Automated gate suite: `tests/integration/test_gate_g1.py`
- [x] Verification script: `backend/scripts/verify_gate_g1.py`

**Verdict:** G1 **PASSED** — June 2026 (Sprint 2 complete)
| **G2 — MVP Demo** | End Sprint 4 | Register → patient → OPD → bill → pay on staging | Extend S4; cut P2 scope |
| **G3 — Clinical Suite** | End Sprint 8 | IPD + lab + pharmacy E2E on staging | Defer pharmacy inventory |
| **G4 — Monetization** | End Sprint 11 | Razorpay trial → paid works; limits enforced | Manual billing interim |
| **G5 — Production Launch** | End Sprint 12 | 10 beta tenants; pen test; isolation tests; runbooks | Soft launch; fix P0s |

### Gate G2 Detailed Checklist (MVP)
- [ ] Self-service tenant registration (UI)
- [ ] Login + role-based redirect
- [ ] Create patient with MRN
- [ ] Search patient by name/phone
- [ ] Book appointment for doctor
- [ ] OPD queue → consultation → e-Rx
- [ ] Generate invoice from visit
- [ ] Collect payment + print receipt
- [ ] RBAC: receptionist cannot void invoice
- [ ] Tenant A cannot see Tenant B patients
- [ ] 3 demo tenants with seed data
- [ ] MVP demo video recorded

### Gate G5 Detailed Checklist (Launch)
- [ ] AWS production deployed (ECS + RDS Multi-AZ)
- [ ] CloudWatch alerts configured
- [ ] Automated backups verified
- [ ] 10 beta tenants onboarded
- [ ] Cross-tenant isolation regression (automated)
- [ ] Rate limiting on auth endpoints
- [ ] Security headers (HSTS, CSP)
- [ ] Deployment runbook published
- [ ] User onboarding guide published
- [ ] P0 bugs = 0

---

## Definition of Done (Per Sprint)

### Code
- [ ] Merged to `main` (or `dev` with PR self-review)
- [ ] No secrets in code
- [ ] Follows `PROJECT_STRUCTURE.md` and `FOLDER_STRUCTURE_FREEZE.md`
- [ ] Matches authoritative docs (SECURITY > RBAC > DATABASE > API)

### Backend
- [ ] `tenant_id` on all new tables and queries
- [ ] `require_permission` on all endpoints
- [ ] Standard API envelope
- [ ] Pydantic validation on all inputs
- [ ] Unit tests for business logic (≥70% new code)
- [ ] Integration test for tenant isolation
- [ ] OpenAPI docs auto-generated

### Frontend
- [ ] Responsive at ≥1024px
- [ ] No raw `fetch` outside `src/api/`
- [ ] Forms use React Hook Form + Zod
- [ ] `PermissionGuard` on restricted actions
- [ ] TypeScript strict — `tsc --noEmit` passes

### Database
- [ ] Alembic migration (never edit applied migrations)
- [ ] RLS enabled on tenant-scoped tables
- [ ] Indexes on FK and search columns
- [ ] Seed data idempotent

### DevOps
- [ ] CI green
- [ ] Deployed to staging
- [ ] Smoke test passed

---

## Risk Register

| ID | Risk | Probability | Impact | Mitigation | Owner |
|----|------|-------------|--------|------------|-------|
| R-01 | Solo developer illness/leave | Medium | High | 20% buffer Months 7–12; defer P2 | PM |
| R-02 | Scope creep | High | High | Strict sprint goals; change → backlog | PM |
| R-03 | Frontend lag behind backend | **High** | **Critical** | Prioritize DS-021 immediately | Dev |
| R-04 | OPD/IPD API spec gaps | Medium | High | Draft specs in S3; use RBAC matrix | Dev |
| R-05 | Doc conflicts (role names, JWT) | Medium | Medium | Authoritative hierarchy enforced | Dev |
| R-06 | RLS not fully implemented | Medium | Critical | Complete DS-010 before patient data | Dev |
| R-07 | No email in dev | Low | Medium | Log-only adapter; defer SES to staging | Dev |
| R-08 | Razorpay integration complexity | Medium | Medium | Sandbox testing in S11; manual fallback | Dev |
| R-09 | Performance at scale | Low | Medium | Index review S9; Redis caching | Dev |
| R-10 | PHI compliance (India) | Medium | High | Audit logs; legal review before launch | PM |
| R-11 | Test suite slow (8+ min) | Medium | Low | Parallelize; mark slow tests | Dev |
| R-12 | Stale planning docs | High | Medium | Update `SDLC Planning/` each sprint | PM |

---

## Sprint Ceremony (Solo Adapted)

| Ceremony | Duration | When |
|----------|----------|------|
| Sprint planning | 1 hr | Friday PM |
| Daily standup (self) | 10 min | Daily |
| Sprint review | 30 min | Friday PM |
| Sprint retro | 30 min | Friday PM |
| Backlog grooming | 1 hr | Mid-sprint Wednesday |

### Sprint Planning Template
1. Review previous sprint velocity
2. Select stories from backlog (≤25 pts)
3. Identify blockers and dependencies
4. Assign Mon–Fri focus areas
5. Update `05_TASK_BACKLOG.md` statuses

---

## Change Control

| Change Type | Process |
|-------------|---------|
| P0 bug in production | Fix immediately; hotfix branch |
| Scope addition | Add to backlog; never current sprint |
| Architecture change | Update authoritative doc first; then code |
| New module | Add to `04_MODULE_PLAN.md`; assign sprint |
| Doc conflict found | Resolve per hierarchy; log in checklist |

---

## Quality Metrics

| Metric | Target | Measured |
|--------|--------|----------|
| Test pass rate | 100% | CI |
| Sprint velocity | 18–25 pts | Sprint review |
| P0 bugs at sprint end | 0 | Bug tracker |
| API response time (p95) | < 500ms | Staging |
| Dashboard load time | < 3s | S9 |
| Tenant isolation | 100% pass | Regression suite |
| Code coverage (new code) | ≥ 70% | pytest-cov |
