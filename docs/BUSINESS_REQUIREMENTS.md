# Business Requirements Document (BRD)

## Multi-Tenant Hospital Management SaaS Platform

| Field | Value |
|-------|-------|
| **Document Version** | 1.0 |
| **Status** | Draft |
| **Last Updated** | June 2026 |
| **Related Documents** | PRD.md, FUNCTIONAL_REQUIREMENTS.md, BILLING_SUBSCRIPTION.md |

---

## 1. Purpose

This document defines the **business requirements** for a cloud-based, multi-tenant Hospital Management System (HMS) delivered as a Software-as-a-Service (SaaS) product. It establishes the business context, objectives, rules, and constraints that govern product decisions, ensuring alignment between business strategy and technical implementation.

---

## 2. Business Context

### 2.1 Problem Statement

Small and medium healthcare providers face significant operational challenges:

- **Fragmented Systems** — Patient records, billing, lab, and pharmacy often run on disconnected tools or paper.
- **High Cost of Ownership** — Traditional on-premise HMS solutions require large upfront investment, dedicated IT staff, and ongoing maintenance.
- **Limited Scalability** — Legacy systems cannot adapt to growing patient volumes or new service lines.
- **Compliance Burden** — Increasing regulatory requirements for data privacy, audit trails, and record retention.
- **Revenue Leakage** — Manual billing processes lead to missed charges, billing errors, and delayed collections.

### 2.2 Business Opportunity

The global digital health market is growing rapidly, with SMB healthcare providers representing an underserved segment. A subscription-based, multi-tenant SaaS model lowers the barrier to entry while generating predictable recurring revenue.

### 2.3 Solution Overview

A unified, cloud-hosted Hospital Management Platform that provides:

- Tenant-isolated clinical and administrative workflows.
- Monthly subscription pricing with tiered plans.
- Rapid onboarding without infrastructure investment.
- Continuous updates and improvements without downtime migrations.

---

## 3. Vision & Mission

### 3.1 Vision

Democratize access to enterprise-grade hospital management technology for every healthcare provider, regardless of size.

### 3.2 Mission

Deliver an affordable, secure, and intuitive SaaS platform that digitizes core hospital operations, improves patient outcomes, and enables sustainable growth for small and medium healthcare organizations.

---

## 4. Strategic Business Objectives

| ID | Objective | Measurable Outcome | Priority |
|----|-----------|-------------------|----------|
| BR-OBJ-01 | Establish market presence in SMB healthcare SaaS | 50 active tenants in Year 1 | High |
| BR-OBJ-02 | Build predictable recurring revenue | ₹50L ARR by end of Year 1 | High |
| BR-OBJ-03 | Achieve product-market fit | NPS ≥ 40, churn < 5% | High |
| BR-OBJ-04 | Reduce healthcare digitization cost by 70% vs. on-premise | Customer cost comparison study | Medium |
| BR-OBJ-05 | Enable 80% paperless operations for adopters | Customer survey post-90 days | Medium |
| BR-OBJ-06 | Build platform extensibility for partner ecosystem | 3+ integration partners by Year 2 | Low |

---

## 5. Target Customers

### 5.1 Customer Segments

#### Segment A: Small & Medium Hospitals

- **Size:** 20–200 beds
- **Staff:** 50–500 employees
- **Needs:** Full HMS — OPD, IPD, lab, pharmacy, billing, reporting
- **Budget:** ₹10,000–₹50,000/month for software
- **Decision Maker:** Hospital Administrator, Owner, CMO

#### Segment B: Clinics & Polyclinics

- **Size:** 1–10 consulting doctors
- **Staff:** 5–30 employees
- **Needs:** OPD, appointments, patient records, billing
- **Budget:** ₹3,000–₹15,000/month
- **Decision Maker:** Clinic Owner, Senior Doctor

#### Segment C: Diagnostic Centers

- **Size:** Standalone or hospital-attached labs
- **Staff:** 10–50 employees
- **Needs:** Test catalog, sample tracking, report generation, billing
- **Budget:** ₹5,000–₹20,000/month
- **Decision Maker:** Lab Director, Center Owner

### 5.2 Customer Buying Journey

```
Awareness → Free Trial (14 days) → Onboarding → Active Use → Renewal/Upsell
```

| Stage | Business Requirement |
|-------|---------------------|
| Awareness | Marketing website, demo videos, case studies |
| Trial | Self-service signup with limited features |
| Onboarding | Guided setup wizard, data import, staff training |
| Active Use | In-app support, help documentation, CS check-ins |
| Renewal | Automated billing, renewal reminders, loyalty incentives |
| Upsell | Module upgrades, additional seats, premium support |

---

## 6. Business Model Requirements

### 6.1 Revenue Model

| Requirement ID | Requirement |
|----------------|-------------|
| BR-REV-01 | Platform shall operate on a **monthly subscription** model with automatic renewal |
| BR-REV-02 | System shall support **tiered pricing plans** differentiated by features, beds, and user seats |
| BR-REV-03 | System shall offer **annual billing** with configurable discount |
| BR-REV-04 | System shall support **add-on purchases** (extra seats, SMS packs, modules) |
| BR-REV-05 | System shall provide **14-day free trial** for new tenants |
| BR-REV-06 | System shall enforce **grace period** (7 days) before suspending overdue accounts |
| BR-REV-07 | System shall support **plan upgrades/downgrades** with prorated billing |

### 6.2 Subscription Tiers

| Tier | Monthly Price | Annual Price | Target Segment |
|------|--------------|--------------|----------------|
| Starter | ₹4,999 | ₹49,990 | Clinics |
| Professional | ₹14,999 | ₹1,49,990 | Small Hospitals |
| Enterprise | Custom | Custom | Medium Hospitals |

### 6.3 Tier Feature Matrix

| Feature | Starter | Professional | Enterprise |
|---------|---------|--------------|------------|
| Max Users | 10 | 50 | 200+ |
| Max Beds | — | 50 | 200+ |
| OPD Module | ✓ | ✓ | ✓ |
| Patient Management | ✓ | ✓ | ✓ |
| Billing | ✓ | ✓ | ✓ |
| IPD Module | — | ✓ | ✓ |
| Laboratory | — | ✓ | ✓ |
| Pharmacy | — | ✓ | ✓ |
| Advanced Reports | — | ✓ | ✓ |
| API Access | — | — | ✓ |
| Custom Branding | — | — | ✓ |
| Priority Support | — | — | ✓ |
| SLA Guarantee | — | — | 99.9% |

---

## 7. Multi-Tenancy Business Requirements

| Requirement ID | Requirement |
|----------------|-------------|
| BR-MT-01 | Each healthcare organization shall operate as an independent **tenant** with isolated data |
| BR-MT-02 | Tenants shall share a common database with **tenant_id** based data isolation |
| BR-MT-03 | Tenant onboarding shall complete within **4 hours** (guided setup) |
| BR-MT-04 | Each tenant shall have a unique **subdomain** or custom domain (Enterprise) |
| BR-MT-05 | Tenant data shall never be visible to or accessible by other tenants |
| BR-MT-06 | Platform super-admin shall manage all tenants without accessing clinical data (unless authorized for support) |
| BR-MT-07 | Tenant suspension shall preserve data for **90 days** before archival |
| BR-MT-08 | Tenant deletion shall follow data retention policy with export option |

---

## 8. Regulatory & Compliance Requirements

| Requirement ID | Requirement | Applicability |
|----------------|-------------|---------------|
| BR-COMP-01 | Platform shall maintain **audit logs** of all user actions per tenant | All tenants |
| BR-COMP-02 | Patient data shall be **encrypted at rest and in transit** | All tenants |
| BR-COMP-03 | Platform shall support **role-based access control** aligned with hospital hierarchy | All tenants |
| BR-COMP-04 | System shall enforce **session timeout** after configurable inactivity period | All tenants |
| BR-COMP-05 | Platform shall comply with **local data protection laws** (e.g., IT Act 2000, DPDP Act 2023 for India) | Region-specific |
| BR-COMP-06 | Patient records shall be **retained** per configurable retention policy (minimum 7 years) | All tenants |
| BR-COMP-07 | System shall support **data export** for tenant offboarding | All tenants |
| BR-COMP-08 | Platform shall provide **Terms of Service** and **Privacy Policy** acceptance during signup | All tenants |

---

## 9. Business Process Requirements

### 9.1 Tenant Lifecycle

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Signup    │───▶│   Trial     │───▶│   Active    │───▶│  Renewed    │
│  (Register) │    │  (14 days)  │    │ (Subscribed)│    │  (Ongoing)  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                          │                  │                    │
                          ▼                  ▼                    ▼
                   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
                   │  Expired    │    │  Suspended  │    │  Cancelled  │
                   │  (No conv.) │    │ (Non-payment)│   │  (Churned)  │
                   └─────────────┘    └─────────────┘    └─────────────┘
```

| Process | Business Rule |
|---------|---------------|
| Signup | Collect organization name, admin email, phone, plan selection |
| Trial | Full feature access for 14 days; no payment required |
| Conversion | Payment method required before trial expiry |
| Active | Full access per subscribed plan |
| Suspension | Read-only access during grace period; full block after grace |
| Cancellation | 30-day notice; data export available for 90 days |
| Reactivation | Allowed within 90 days with outstanding payment cleared |

### 9.2 Patient Lifecycle (Per Tenant)

| Process | Business Rule |
|---------|---------------|
| Registration | Unique MRN per tenant; duplicate detection by phone/name |
| Visit | OPD or IPD encounter linked to patient record |
| Treatment | Clinical notes, prescriptions, lab orders captured |
| Billing | Services charged per tenant's service master |
| Discharge | IPD discharge summary generated; final billing settled |
| Follow-up | Appointment scheduled; reminders sent |

### 9.3 Billing Lifecycle (Hospital Operations)

| Process | Business Rule |
|---------|---------------|
| Service Definition | Tenant admin configures chargeable services |
| Charge Capture | Services linked to patient encounter automatically or manually |
| Invoice Generation | Itemized bill with tax calculations per tenant config |
| Payment | Multiple payment modes accepted; partial payments allowed |
| Receipt | Auto-generated receipt on payment confirmation |
| Reporting | Daily collection, outstanding, and revenue reports |

---

## 10. Stakeholder Requirements

### 10.1 Stakeholder Map

| Stakeholder | Interest | Influence | Engagement |
|-------------|----------|-----------|------------|
| Hospital Owners | ROI, cost savings | High | Monthly business reviews |
| Hospital Administrators | Operations efficiency | High | Onboarding, training |
| Clinical Staff | Ease of use, patient care | Medium | UX feedback, training |
| Patients (indirect) | Service quality, wait times | Low | Satisfaction surveys |
| Platform Investors | Revenue growth, scalability | High | Quarterly reports |
| Regulatory Bodies | Compliance, data protection | High | Audit cooperation |
| Integration Partners | API access, data exchange | Medium | Partner program |

### 10.2 Stakeholder-Specific Requirements

| Stakeholder | Key Requirement |
|-------------|-----------------|
| Hospital Owner | Clear ROI dashboard showing cost savings and revenue impact |
| Administrator | Single pane of glass for all departments |
| Doctor | Patient history accessible within 2 clicks |
| Receptionist | Patient registration in < 2 minutes |
| Billing Staff | Accurate invoices with zero manual calculation |
| Platform Operator | Tenant health dashboard, MRR tracking, churn alerts |

---

## 11. Business Rules

| Rule ID | Rule | Category |
|---------|------|----------|
| BR-RULE-01 | Each tenant must have exactly one primary admin account | Tenancy |
| BR-RULE-02 | MRN is unique within a tenant, not globally | Patient |
| BR-RULE-03 | Billing amounts use tenant's configured currency | Finance |
| BR-RULE-04 | Deactivated users cannot log in but their audit history is preserved | Security |
| BR-RULE-05 | Subscription limits (users, beds) are enforced at login and resource creation | Subscription |
| BR-RULE-06 | Trial tenants are limited to 5 users and 100 patient records | Subscription |
| BR-RULE-07 | Downgrade takes effect at next billing cycle | Subscription |
| BR-RULE-08 | All monetary transactions require an authenticated user | Finance |
| BR-RULE-09 | Patient consent must be recorded before data processing (where required by law) | Compliance |
| BR-RULE-10 | Platform maintenance windows communicated 48 hours in advance | Operations |

---

## 12. Key Business Metrics & KPIs

### 12.1 Revenue Metrics

| Metric | Definition | Year 1 Target |
|--------|------------|---------------|
| MRR | Monthly Recurring Revenue | ₹4,00,000 |
| ARR | Annual Recurring Revenue | ₹48,00,000 |
| ARPU | Average Revenue Per User (tenant) | ₹12,000/month |
| Expansion Revenue | Revenue from upsells and add-ons | 15% of MRR |

### 12.2 Customer Metrics

| Metric | Definition | Year 1 Target |
|--------|------------|---------------|
| Active Tenants | Paying tenants with login in last 30 days | 50 |
| Churn Rate | % tenants cancelling per month | < 5% |
| Trial Conversion | % trials converting to paid | > 25% |
| NPS | Net Promoter Score | ≥ 40 |
| CSAT | Customer Satisfaction Score | ≥ 4.0/5.0 |

### 12.3 Operational Metrics

| Metric | Definition | Year 1 Target |
|--------|------------|---------------|
| Onboarding Time | Hours from signup to first patient record | < 4 hours |
| Support Response Time | Time to first response on support tickets | < 4 hours |
| Support Resolution Time | Time to resolve support tickets | < 24 hours |
| Uptime | Platform availability | 99.9% |

---

## 13. Business Risks

| Risk ID | Risk | Business Impact | Likelihood | Mitigation Strategy |
|---------|------|-----------------|------------|---------------------|
| BR-RISK-01 | Low trial-to-paid conversion | Revenue shortfall | Medium | Improve onboarding, in-trial engagement emails |
| BR-RISK-02 | High customer churn | Revenue instability | Medium | Customer success program, feature stickiness |
| BR-RISK-03 | Pricing too high for SMB market | Low adoption | Medium | Competitive analysis, flexible tiers, annual discounts |
| BR-RISK-04 | Pricing too low | Unsustainable unit economics | Low | Monitor CAC:LTV, adjust tiers |
| BR-RISK-05 | Regulatory changes | Compliance cost increase | Medium | Legal monitoring, modular compliance architecture |
| BR-RISK-06 | Data breach | Reputation damage, legal liability | Low | Security-first architecture, insurance, incident response plan |
| BR-RISK-07 | Key competitor enters market | Market share loss | Medium | Differentiation via UX, pricing, local support |
| BR-RISK-08 | Slow sales cycle | Cash flow pressure | Medium | Free trial, self-service signup, inside sales |
| BR-RISK-09 | Customer data migration complexity | Onboarding friction | High | CSV import tools, migration assistance service |
| BR-RISK-10 | Dependency on payment gateway | Billing disruption | Low | Multi-gateway support, manual payment fallback |

---

## 14. Scope Boundaries

### 14.1 In Scope

- SaaS platform for hospital management (clinical + administrative).
- Multi-tenant architecture with subscription billing.
- Web-based access for all user roles.
- Core modules: Patient, OPD, Billing (MVP); IPD, Lab, Pharmacy (Phase 2).
- Tenant self-service administration.
- Platform-level tenant and subscription management.

### 14.2 Out of Scope

- Hospital hardware procurement (beds, equipment).
- Medical device integration.
- Insurance claim processing (full TPA integration — Phase 3).
- Government health scheme integration (Phase 3+).
- Custom software development for individual tenants.
- On-premise deployment option (MVP).

---

## 15. Future Business Scope

| Initiative | Business Value | Target Phase |
|------------|---------------|--------------|
| Partner marketplace (labs, pharmacies) | Ecosystem revenue, stickiness | Phase 3 |
| White-label offering for hospital chains | Premium pricing, B2B2B model | Phase 4 |
| AI-powered revenue optimization | Differentiation, upsell | Phase 4 |
| International expansion (Middle East, Africa) | Market growth | Phase 5 |
| Government tender participation | Large contract opportunities | Phase 5 |
| Acquisition of complementary health-tech startups | Capability expansion | Year 2+ |

---

## 16. Acceptance Criteria (Business Level)

| # | Criterion | Verification Method |
|---|-----------|---------------------|
| 1 | New tenant can sign up, configure organization, and register first patient within 4 hours | Onboarding test |
| 2 | Subscription billing processes automatically on renewal date | Billing integration test |
| 3 | Tenant data is fully isolated from other tenants | Security audit |
| 4 | Overdue accounts are suspended per grace period rules | Billing workflow test |
| 5 | Plan limits (users, beds) are enforced | Limit enforcement test |
| 6 | Financial reports match transactional data | Reconciliation test |
| 7 | Audit logs capture all critical user actions | Compliance audit |
| 8 | Data export produces complete tenant dataset | Export test |

---

## 17. Glossary

| Term | Definition |
|------|------------|
| **Tenant** | A healthcare organization (hospital, clinic, diagnostic center) using the platform |
| **MRN** | Medical Record Number — unique patient identifier within a tenant |
| **OPD** | Outpatient Department |
| **IPD** | Inpatient Department |
| **MRR** | Monthly Recurring Revenue |
| **ARR** | Annual Recurring Revenue |
| **Churn** | Rate at which customers cancel their subscription |
| **NPS** | Net Promoter Score — customer loyalty metric |
| **RBAC** | Role-Based Access Control |
| **SaaS** | Software as a Service |

---

## 18. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | June 2026 | Product Team | Initial BRD |
