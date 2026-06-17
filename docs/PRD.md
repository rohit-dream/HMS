# Product Requirements Document (PRD)

## Multi-Tenant Hospital Management SaaS Platform

| Field | Value |
|-------|-------|
| **Document Version** | 1.0 |
| **Status** | Draft |
| **Last Updated** | June 2026 |
| **Product Owner** | Product Management |
| **Stakeholders** | Engineering, Sales, Customer Success, Compliance |

---

## 1. Executive Summary

This document defines the product requirements for a **Multi-Tenant Hospital Management SaaS Platform** designed to serve small and medium hospitals, clinics, and diagnostic centers. The platform delivers end-to-end clinical and administrative workflows through a cloud-native, subscription-based model with tenant-isolated data on a shared database architecture.

The product aims to replace fragmented paper-based and legacy on-premise systems with a unified, affordable, and compliant digital health platform that scales from a single-clinic practice to a multi-department hospital.

---

## 2. Vision

**To become the most trusted, affordable, and intelligent hospital management platform for emerging healthcare providers—empowering every clinic and hospital to deliver world-class patient care through modern, connected, and data-driven operations.**

We envision a future where:

- Every small and medium healthcare facility operates on a single, integrated digital platform.
- Clinical, operational, and financial data flows seamlessly across departments.
- Subscription pricing removes the capital barrier to enterprise-grade healthcare software.
- AI-assisted insights improve clinical decisions, operational efficiency, and revenue integrity.
- Multi-tenant architecture enables rapid onboarding while maintaining strict data isolation and regulatory compliance.

---

## 3. Product Goals

### 3.1 Primary Goals

| # | Goal | Success Indicator |
|---|------|-------------------|
| G1 | Enable rapid tenant onboarding (< 24 hours) | Time-to-first-patient-record < 1 business day |
| G2 | Deliver core HMS workflows for SMB healthcare | 80% of daily operations handled in-platform |
| G3 | Ensure tenant data isolation and security | Zero cross-tenant data leakage incidents |
| G4 | Achieve predictable recurring revenue | 90%+ subscription renewal rate |
| G5 | Reduce operational overhead for healthcare staff | 30% reduction in administrative time (self-reported) |

### 3.2 Secondary Goals

- Support multi-location facilities under a single tenant account.
- Provide role-based access aligned with hospital hierarchy.
- Enable self-service subscription management and billing.
- Build an extensible API layer for third-party integrations (labs, pharmacies, insurance).
- Establish a foundation for AI-powered clinical and operational features.

---

## 4. Target Market & Customer Segments

### 4.1 Primary Segments

| Segment | Profile | Pain Points | Value Proposition |
|---------|---------|-------------|-------------------|
| **Small Hospitals** | 20–100 beds, 50–300 staff | Legacy systems, high IT cost, poor interoperability | Affordable SaaS with full HMS modules |
| **Clinics** | 1–10 doctors, outpatient focus | Paper records, appointment chaos, billing errors | Simple OPD + billing in one platform |
| **Diagnostic Centers** | Lab/imaging focused | Sample tracking, report delivery, TAT management | Specialized lab & radiology workflows |

### 4.2 Geographic Focus (Initial)

- Primary: India and South/Southeast Asia (SMB healthcare market).
- Expansion: Middle East and Africa (Phase 2).

### 4.3 Ideal Customer Profile (ICP)

- 10–500 daily patient encounters.
- No dedicated IT department or limited IT capacity.
- Willing to adopt cloud SaaS with monthly billing.
- Requires compliance with local healthcare data regulations.
- Seeking digitization within 3–6 months.

---

## 5. User Personas

### 5.1 Dr. Priya Sharma — Chief Medical Officer (Hospital Administrator)

| Attribute | Detail |
|-----------|--------|
| **Role** | CMO / Medical Director |
| **Age** | 45 |
| **Goals** | Clinical quality, regulatory compliance, operational visibility |
| **Frustrations** | Siloed departments, delayed reports, no real-time dashboards |
| **Needs** | Executive dashboards, audit trails, department performance metrics |
| **Tech Savviness** | Moderate |

### 5.2 Rajesh Kumar — Hospital Administrator / Operations Manager

| Attribute | Detail |
|-----------|--------|
| **Role** | Hospital Administrator |
| **Age** | 38 |
| **Goals** | Efficient operations, cost control, staff productivity |
| **Frustrations** | Manual scheduling, inventory stockouts, billing disputes |
| **Needs** | Bed management, inventory alerts, revenue reports |
| **Tech Savviness** | Moderate to High |

### 5.3 Anjali Desai — Front Desk / Receptionist

| Attribute | Detail |
|-----------|--------|
| **Role** | Reception / Registration |
| **Age** | 28 |
| **Goals** | Fast patient check-in, accurate appointments |
| **Frustrations** | Long queues, duplicate patient records, phone-heavy scheduling |
| **Needs** | Quick registration, appointment calendar, patient search |
| **Tech Savviness** | Low to Moderate |

### 5.4 Dr. Vikram Patel — Consulting Physician

| Attribute | Detail |
|-----------|--------|
| **Role** | Doctor (OPD / IPD) |
| **Age** | 42 |
| **Goals** | Efficient consultations, complete patient history at fingertips |
| **Frustrations** | Incomplete records, illegible prescriptions, no lab history |
| **Needs** | EMR, e-prescription, lab results, clinical notes |
| **Tech Savviness** | Low to Moderate |

### 5.5 Sunita Nair — Billing & Finance Executive

| Attribute | Detail |
|-----------|--------|
| **Role** | Billing / Accounts |
| **Age** | 35 |
| **Goals** | Accurate invoicing, payment tracking, insurance claims |
| **Frustrations** | Manual calculations, reconciliation errors, delayed collections |
| **Needs** | Automated billing, payment modes, financial reports |
| **Tech Savviness** | Moderate |

### 5.6 Amit Singh — Lab Technician

| Attribute | Detail |
|-----------|--------|
| **Role** | Laboratory Staff |
| **Age** | 30 |
| **Goals** | Accurate sample processing, timely report generation |
| **Frustrations** | Lost samples, manual result entry, delayed report delivery |
| **Needs** | Sample tracking, result entry, report templates |
| **Tech Savviness** | Moderate |

### 5.7 Platform Super Admin (Internal)

| Attribute | Detail |
|-----------|--------|
| **Role** | SaaS Platform Operator |
| **Goals** | Tenant provisioning, subscription management, platform health |
| **Needs** | Tenant admin console, usage analytics, billing oversight |

---

## 6. Business Objectives

| Objective | Description | Timeline |
|-----------|-------------|----------|
| **BO-01** | Launch MVP with core OPD, patient, billing, and tenant management | Q3 2026 |
| **BO-02** | Acquire 50 paying tenants within 6 months of launch | Q1 2027 |
| **BO-03** | Achieve ₹50L ARR by end of Year 1 | Q2 2027 |
| **BO-04** | Maintain < 5% monthly churn | Ongoing |
| **BO-05** | Achieve NPS ≥ 40 among hospital administrators | Q4 2027 |
| **BO-06** | Reduce customer onboarding time to < 4 hours (guided) | Q4 2026 |

---

## 7. Business Model

### 7.1 Revenue Model

- **Monthly Subscription SaaS** — recurring revenue per tenant.
- Tiered plans based on bed count, user seats, and module access.
- Annual billing option with discount (10–15%).

### 7.2 Subscription Tiers (Indicative)

| Tier | Target | Beds | Users | Modules | Price Range |
|------|--------|------|-------|---------|-------------|
| **Starter** | Clinics | N/A | Up to 10 | OPD, Patient, Billing | ₹4,999/mo |
| **Professional** | Small Hospitals | Up to 50 | Up to 50 | + IPD, Lab, Pharmacy | ₹14,999/mo |
| **Enterprise** | Medium Hospitals | Up to 200 | Up to 200 | Full suite + API | Custom |

### 7.3 Add-On Revenue

- Additional user seats.
- SMS/WhatsApp notification packs.
- Premium support SLA.
- Custom integrations and white-labeling (Enterprise).

---

## 8. Product Features

### 8.1 Platform & Multi-Tenancy

| Feature | Description | Priority |
|---------|-------------|----------|
| Tenant Provisioning | Self-service and admin-assisted tenant creation | P0 |
| Tenant Isolation | `tenant_id` based row-level data isolation | P0 |
| Subscription Management | Plan selection, upgrades, renewals | P0 |
| Organization Profile | Hospital branding, settings, locations | P0 |
| User & Role Management | RBAC with predefined hospital roles | P0 |

### 8.2 Patient Management

| Feature | Description | Priority |
|---------|-------------|----------|
| Patient Registration | Demographics, contact, ID proof, insurance | P0 |
| Patient Search | Fast lookup by name, phone, MRN | P0 |
| Medical Record Number (MRN) | Auto-generated unique patient identifier per tenant | P0 |
| Patient History | Visit history, allergies, chronic conditions | P0 |
| Document Attachments | Upload reports, scans, consent forms | P1 |

### 8.3 Outpatient (OPD)

| Feature | Description | Priority |
|---------|-------------|----------|
| Appointment Scheduling | Doctor-wise calendar, slot management | P0 |
| Queue Management | Token-based waiting queue | P0 |
| Consultation Notes | Clinical notes, diagnosis, vitals | P0 |
| E-Prescription | Medication orders with dosage instructions | P0 |
| Referrals | Internal and external referral tracking | P1 |

### 8.4 Inpatient (IPD)

| Feature | Description | Priority |
|---------|-------------|----------|
| Admission Management | Bed assignment, admission workflow | P1 |
| Bed Management | Ward/bed availability dashboard | P1 |
| Nursing Notes | Vitals charting, nursing care plans | P1 |
| Discharge Summary | Structured discharge documentation | P1 |
| Transfer Management | Ward/department transfers | P2 |

### 8.5 Laboratory

| Feature | Description | Priority |
|---------|-------------|----------|
| Test Catalog | Configurable lab test master | P1 |
| Sample Collection | Barcode/sample ID tracking | P1 |
| Result Entry | Technician result input with validation | P1 |
| Report Generation | PDF/HTML lab reports with branding | P1 |
| Critical Value Alerts | Notify doctor on abnormal results | P2 |

### 8.6 Pharmacy

| Feature | Description | Priority |
|---------|-------------|----------|
| Drug Master | Medicine catalog with generics | P1 |
| Prescription Fulfillment | Dispense against e-prescriptions | P1 |
| Inventory Management | Stock in/out, reorder alerts | P1 |
| Purchase Orders | Supplier management | P2 |

### 8.7 Billing & Finance

| Feature | Description | Priority |
|---------|-------------|----------|
| Service Master | Configurable charge items | P0 |
| OPD/IPD Billing | Itemized invoices | P0 |
| Payment Collection | Cash, card, UPI, insurance | P0 |
| Receipts & Invoices | Printable/PDF generation | P0 |
| Financial Reports | Daily collection, outstanding, revenue | P1 |
| Insurance / TPA | Claim tracking (basic) | P2 |

### 8.8 Reporting & Analytics

| Feature | Description | Priority |
|---------|-------------|----------|
| Operational Dashboard | Key metrics at a glance | P1 |
| Department Reports | OPD, IPD, lab, pharmacy summaries | P1 |
| Export | CSV/PDF export for reports | P1 |
| Custom Report Builder | User-defined reports | P3 |

### 8.9 Administration

| Feature | Description | Priority |
|---------|-------------|----------|
| Staff Management | Employee records, departments | P0 |
| Audit Logs | User action tracking per tenant | P0 |
| System Configuration | Tenant-level settings and masters | P0 |
| Notification Engine | Email/SMS alerts | P1 |

---

## 9. Scope

### 9.1 In Scope (MVP — Phase 1)

- Multi-tenant platform with shared database and `tenant_id` isolation.
- Tenant onboarding, subscription, and billing (platform-level).
- User authentication, RBAC, and audit logging.
- Patient registration and search.
- OPD: appointments, queue, consultation, e-prescription.
- Billing: service master, invoicing, payments, receipts.
- Basic reporting and admin dashboard.
- Responsive web application (React + TypeScript + TailwindCSS).
- REST API (FastAPI + Python).
- SQL database with migration support.

### 9.2 Out of Scope (MVP)

- Native mobile applications (iOS/Android).
- Telemedicine / video consultation.
- Full insurance/TPA integration.
- HL7/FHIR interoperability.
- AI/ML clinical decision support.
- Hardware integrations (biometric, lab analyzers).
- Multi-language support (beyond English; Hindi in Phase 2).
- Offline mode.

### 9.3 Assumptions

- Tenants have reliable internet connectivity.
- Users access the platform via modern web browsers (Chrome, Edge, Firefox).
- Payment gateway integration available in target geography.
- Regulatory compliance requirements are defined per deployment region.
- Initial deployment on a single cloud region.

### 9.4 Constraints

- Shared database multi-tenancy (no database-per-tenant in MVP).
- Monthly subscription billing model only at launch.
- English UI for MVP.
- Maximum 200 concurrent users per tenant (MVP target).

---

## 10. Future Scope

| Phase | Features | Timeline |
|-------|----------|----------|
| **Phase 2** | IPD, Laboratory, Pharmacy modules | Q4 2026 |
| **Phase 3** | Insurance/TPA, advanced analytics, Hindi localization | Q1 2027 |
| **Phase 4** | AI features: appointment optimization, revenue leakage detection | Q2 2027 |
| **Phase 5** | Mobile apps, telemedicine, HL7/FHIR APIs | Q3 2027 |
| **Phase 6** | Multi-region deployment, white-label, marketplace integrations | Q4 2027 |

---

## 11. Technical Architecture Summary

| Layer | Technology |
|-------|------------|
| Frontend | React.js, TypeScript, TailwindCSS |
| Backend | Python, FastAPI |
| Database | SQL (PostgreSQL recommended) |
| Architecture | Multi-tenant, shared database, `tenant_id` row isolation |
| Auth | JWT-based authentication with tenant context |
| Deployment | Cloud-native (containerized), CI/CD pipeline |

> Detailed architecture is documented in `SYSTEM_ARCHITECTURE.md`, `MULTI_TENANT_DESIGN.md`, and `DATABASE_DESIGN.md`.

---

## 12. Key Performance Indicators (KPIs)

### 12.1 Business KPIs

| KPI | Target (Year 1) | Measurement |
|-----|-----------------|-------------|
| Monthly Recurring Revenue (MRR) | ₹4L+ by Month 12 | Billing system |
| Customer Acquisition Cost (CAC) | < ₹15,000 | Sales analytics |
| Customer Lifetime Value (LTV) | > ₹1,50,000 | Cohort analysis |
| LTV:CAC Ratio | > 3:1 | Derived |
| Monthly Churn Rate | < 5% | Subscription data |
| Net Revenue Retention | > 100% | Upsell tracking |
| Trial-to-Paid Conversion | > 25% | Funnel analytics |

### 12.2 Product KPIs

| KPI | Target | Measurement |
|-----|--------|-------------|
| Time to Onboard (new tenant) | < 4 hours | Onboarding tracker |
| Daily Active Users (DAU) per tenant | > 60% of licensed seats | Analytics |
| Feature Adoption (core modules) | > 70% within 30 days | Usage telemetry |
| Patient Records Created / Month | Growth ≥ 15% MoM | Database metrics |
| Support Ticket Volume | < 2 tickets/tenant/month | Helpdesk |
| Net Promoter Score (NPS) | ≥ 40 | Quarterly survey |

### 12.3 Technical KPIs

| KPI | Target | Measurement |
|-----|--------|-------------|
| API Uptime | 99.9% | Monitoring |
| P95 API Response Time | < 500ms | APM |
| P95 Page Load Time | < 3 seconds | RUM |
| Zero Cross-Tenant Data Leaks | 0 incidents | Security audits |
| Mean Time to Recovery (MTTR) | < 1 hour | Incident logs |

---

## 13. Risks & Mitigations

| # | Risk | Impact | Probability | Mitigation |
|---|------|--------|-------------|------------|
| R1 | Cross-tenant data leakage | Critical | Low | Mandatory `tenant_id` filters, middleware enforcement, penetration testing |
| R2 | Slow adoption by non-tech staff | High | Medium | Intuitive UX, role-based simplified views, training materials |
| R3 | Regulatory non-compliance | Critical | Medium | Compliance review per region, audit logs, data encryption |
| R4 | Subscription payment failures | Medium | Medium | Dunning workflows, grace periods, multiple payment methods |
| R5 | Performance degradation at scale | High | Medium | Query optimization, indexing, connection pooling, load testing |
| R6 | Feature creep delaying MVP | High | High | Strict scope governance, phased roadmap, MVP-first culture |
| R7 | Competitor pricing pressure | Medium | High | Value differentiation, tiered pricing, customer success focus |
| R8 | Data loss / corruption | Critical | Low | Automated backups, point-in-time recovery, disaster recovery plan |
| R9 | Key personnel dependency | Medium | Medium | Documentation, code reviews, knowledge sharing |
| R10 | Integration complexity with legacy systems | Medium | Medium | API-first design, phased integration, CSV import/export |

---

## 14. Success Criteria

The product will be considered successful when:

1. MVP is deployed to production with ≥ 10 paying tenants.
2. Core workflows (registration → consultation → billing) complete in < 5 minutes.
3. No critical security incidents in first 6 months.
4. Customer satisfaction (CSAT) ≥ 4.0/5.0.
5. Platform uptime ≥ 99.9% over any rolling 30-day period.

---

## 15. Dependencies

| Dependency | Owner | Status |
|------------|-------|--------|
| Cloud infrastructure provisioning | DevOps | Planned |
| Payment gateway integration | Engineering + Finance | Planned |
| SMS/Email provider | Engineering | Planned |
| Legal review (terms, privacy, HIPAA/local compliance) | Legal | Planned |
| UI/UX design system | Design | Planned |
| Beta customer recruitment | Sales | Planned |

---

## 16. Approval & Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner | | | |
| Engineering Lead | | | |
| Business Stakeholder | | | |
| Compliance Officer | | | |

---

## 17. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | June 2026 | Product Team | Initial PRD |
