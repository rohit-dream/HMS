# Advanced Features Roadmap

## Multi-Tenant Hospital Management SaaS Platform

| Field | Value |
|-------|-------|
| **Document Version** | 1.0 |
| **Status** | Approved for Post-MVP Planning |
| **Last Updated** | June 2026 |
| **Planning Horizon** | Post-MVP (Q1 2027 – Q4 2028) |
| **Related Documents** | ROADMAP.md, PRD.md, BUSINESS_REQUIREMENTS.md, DATABASE_DESIGN.md, RBAC_DESIGN.md, AI_FEATURES.md |

---

## 1. Document Purpose & Scope

This document is the **authoritative post-MVP feature repository** for the Multi-Tenant Hospital Management SaaS Platform. All features documented here are **explicitly excluded from MVP development** (Phases 1–3).

### 1.1 Activation Criteria

Advanced features enter development only after:

| Gate | Requirement |
|------|-------------|
| G1 | Core HMS modules completed (OPD, Patient, Billing, IPD, Lab, Pharmacy) |
| G2 | MVP deployed to production with 99.9% uptime |
| G3 | Minimum 25 hospitals onboarded and actively using the platform |
| G4 | Paying customer base established with < 7% monthly churn |
| G5 | Phase gate review approved by Product & Engineering leadership |

### 1.2 Technology Context

| Layer | Technology |
|-------|------------|
| Database | PostgreSQL 14+ (shared DB, `tenant_id` row isolation) |
| Backend | FastAPI (Python), Pydantic v2, REST API v1 |
| Frontend | React.js + TypeScript + TailwindCSS |
| Auth | JWT with `tenant_id` claim, RBAC enforcement |
| Billing | Monthly subscription (Starter / Professional / Enterprise) |

### 1.3 Feature Specification Template

Each feature below includes 17 specification fields: Feature Name, Category, Business Problem Solved, Business Value, Target Users, Development Priority, Complexity Level, Estimated Development Effort, Required Database Tables, Required APIs, Required UI Screens, RBAC Impact, Multi-Tenant Considerations, Dependencies, Revenue Impact, Recommended Subscription Plan, and Future Enhancements.

### 1.4 Priority Legend

| Priority | Meaning |
|----------|---------|
| P1 | High — strong revenue or retention impact; build early in phase |
| P2 | Medium — valuable differentiator; build mid-phase |
| P3 | Low — niche or enterprise-only; build late in phase |

### 1.5 Complexity & Effort Legend

| Complexity | Typical Effort |
|------------|----------------|
| Low | 2–4 developer-weeks |
| Medium | 5–10 developer-weeks |
| High | 11–20+ developer-weeks |

---

## 2. PHASE 4 – PREMIUM HOSPITAL MODULES

**Timeline:** Q1–Q2 2027 (post-MVP)  
**Theme:** Specialized clinical departments for medium hospitals  
**Target:** Upsell Professional tenants to Enterprise; attract 50+ bed hospitals

---

### 2.1 Operation Theater Management

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | Operation Theater (OT) Management |
| 2 | **Category** | Premium Clinical Module |
| 3 | **Business Problem Solved** | Surgical scheduling, OT resource allocation, and perioperative documentation are managed on paper or spreadsheets, causing double-bookings, equipment conflicts, and billing gaps. |
| 4 | **Business Value** | Increases surgical throughput by 15–20%; reduces OT idle time; captures complete surgical billing; improves compliance with surgical audit requirements. |
| 5 | **Target Users** | Surgeons, OT Nurses, Anesthetists, Hospital Admin, Billing Staff |
| 6 | **Development Priority** | P1 |
| 7 | **Complexity Level** | High |
| 8 | **Estimated Development Effort** | 14–16 developer-weeks |
| 9 | **Required Database Tables** | `clinical.ot_rooms`, `clinical.ot_schedules`, `clinical.surgical_procedures`, `clinical.ot_bookings`, `clinical.pre_op_assessments`, `clinical.intra_op_records`, `clinical.post_op_notes`, `clinical.ot_equipment`, `clinical.ot_equipment_allocations`, `billing.ot_charge_master` |
| 10 | **Required APIs** | `GET/POST /api/v1/ot-rooms`, `GET/POST /api/v1/ot-schedules`, `POST /api/v1/ot-bookings`, `PATCH /api/v1/ot-bookings/{id}/status`, `POST /api/v1/ot-bookings/{id}/pre-op`, `POST /api/v1/ot-bookings/{id}/intra-op`, `POST /api/v1/ot-bookings/{id}/post-op`, `GET /api/v1/ot-availability`, `POST /api/v1/ot-bookings/{id}/bill` |
| 11 | **Required UI Screens** | OT Room Master, OT Calendar/Scheduler, Booking Form, Pre-Op Assessment, Intra-Op Record, Post-Op Notes, OT Dashboard (utilization), OT Billing Summary |
| 12 | **RBAC Impact** | New permissions: `ot:read`, `ot:schedule`, `ot:clinical_write`, `ot:bill`. New role template: `ot_nurse`, `anesthetist`. Surgeons inherit `ot:clinical_write`. |
| 13 | **Multi-Tenant Considerations** | All OT tables include `tenant_id`; OT room codes unique per tenant; schedules isolated; cross-tenant OT sharing not supported. |
| 14 | **Dependencies** | IPD Module, Patient Management, Billing Module, Staff/Doctor profiles, Admission module |
| 15 | **Revenue Impact** | High — primary Enterprise upsell driver; estimated +₹5,000–₹10,000/month per tenant |
| 16 | **Recommended Subscription Plan** | Enterprise (add-on available for Professional at premium) |
| 17 | **Future Enhancements** | Anesthesia machine integration, surgical video recording links, implant/consumable tracking, robotic surgery scheduling |

---

### 2.2 ICU Management

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | ICU Management |
| 2 | **Category** | Premium Clinical Module |
| 3 | **Business Problem Solved** | Critical care patients require continuous monitoring, ventilator tracking, and hourly vitals documentation that generic IPD workflows cannot support. |
| 4 | **Business Value** | Reduces documentation time for ICU nurses by 30%; enables real-time bed occupancy visibility; supports critical care billing accuracy; improves mortality/morbidity audit readiness. |
| 5 | **Target Users** | ICU Doctors, ICU Nurses, Hospital Admin, Billing Staff |
| 6 | **Development Priority** | P1 |
| 7 | **Complexity Level** | High |
| 8 | **Estimated Development Effort** | 12–14 developer-weeks |
| 9 | **Required Database Tables** | `clinical.icu_beds`, `clinical.icu_admissions`, `clinical.icu_vitals` (hourly), `clinical.icu_nursing_charts`, `clinical.ventilator_records`, `clinical.icu_medication_infusions`, `clinical.icu_scores` (APACHE/SOFA), `clinical.icu_transfers` |
| 10 | **Required APIs** | `GET/POST /api/v1/icu-beds`, `POST /api/v1/icu-admissions`, `POST /api/v1/icu-admissions/{id}/vitals`, `POST /api/v1/icu-admissions/{id}/ventilator`, `POST /api/v1/icu-admissions/{id}/infusions`, `GET /api/v1/icu-dashboard`, `POST /api/v1/icu-admissions/{id}/transfer`, `POST /api/v1/icu-admissions/{id}/discharge` |
| 11 | **Required UI Screens** | ICU Bed Dashboard, ICU Admission Form, Hourly Vitals Chart, Ventilator Record, Infusion Pump Log, ICU Nursing Chart, Severity Score Calculator, ICU Discharge Summary |
| 12 | **RBAC Impact** | New permissions: `icu:read`, `icu:write`, `icu:discharge`. Role extensions for `nurse` (ICU write) and `doctor` (ICU clinical). |
| 13 | **Multi-Tenant Considerations** | ICU beds are a subtype of IPD beds scoped by `tenant_id`; vitals time-series partitioned by tenant for query performance. |
| 14 | **Dependencies** | IPD Module, Bed Management, Patient Management, Billing (daily ICU charges) |
| 15 | **Revenue Impact** | High — critical for 50+ bed hospitals; +₹4,000–₹8,000/month upsell |
| 16 | **Recommended Subscription Plan** | Enterprise |
| 17 | **Future Enhancements** | Bedside monitor auto-import, predictive deterioration alerts (AI), tele-ICU support, infection control surveillance |

---

### 2.3 Emergency Department Management

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | Emergency Department (ED) Management |
| 2 | **Category** | Premium Clinical Module |
| 3 | **Business Problem Solved** | Emergency triage, rapid patient flow, and medico-legal documentation require specialized workflows distinct from scheduled OPD visits. |
| 4 | **Business Value** | Reduces ED wait times through triage-based queue prioritization; improves trauma documentation compliance; accelerates ED-to-IPD/OT transitions. |
| 5 | **Target Users** | ED Doctors, Triage Nurses, Reception Staff, Hospital Admin |
| 6 | **Development Priority** | P1 |
| 7 | **Complexity Level** | Medium |
| 8 | **Estimated Development Effort** | 10–12 developer-weeks |
| 9 | **Required Database Tables** | `clinical.ed_visits`, `clinical.ed_triage_records`, `clinical.ed_triage_categories`, `clinical.ed_treatment_bays`, `clinical.ed_procedures`, `clinical.ed_observations`, `clinical.ed_dispositions`, `clinical.ed_mlc_records` (medico-legal) |
| 10 | **Required APIs** | `POST /api/v1/ed-visits`, `POST /api/v1/ed-visits/{id}/triage`, `GET /api/v1/ed-queue`, `PATCH /api/v1/ed-visits/{id}/status`, `POST /api/v1/ed-visits/{id}/treatment`, `POST /api/v1/ed-visits/{id}/disposition`, `POST /api/v1/ed-visits/{id}/admit`, `GET /api/v1/ed-dashboard` |
| 11 | **Required UI Screens** | ED Registration (walk-in), Triage Assessment, ED Queue Board (color-coded), Treatment Bay Assignment, ED Clinical Notes, Disposition (discharge/admit/refer), MLC Documentation, ED Dashboard |
| 12 | **RBAC Impact** | New permissions: `ed:register`, `ed:triage`, `ed:clinical_write`, `ed:disposition`. Triage nurses get `ed:triage`; ED doctors get full ED clinical access. |
| 13 | **Multi-Tenant Considerations** | ED queue is tenant-scoped real-time data; triage category configs stored in `tenant_settings`; no cross-tenant patient transfers. |
| 14 | **Dependencies** | Patient Management, OPD Module, IPD Module (for admissions), Billing |
| 15 | **Revenue Impact** | Medium-High — required for full-service hospitals; +₹3,000–₹6,000/month |
| 16 | **Recommended Subscription Plan** | Professional (basic ED) / Enterprise (full ED with MLC) |
| 17 | **Future Enhancements** | Ambulance pre-arrival alerts, mass casualty incident mode, ED wait time public display, integration with national emergency registries |

---

### 2.4 Blood Bank Management

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | Blood Bank Management |
| 2 | **Category** | Premium Clinical Module |
| 3 | **Business Problem Solved** | Blood inventory tracking, donor management, cross-matching, and issue/return workflows are error-prone when managed manually, risking patient safety and regulatory non-compliance. |
| 4 | **Business Value** | Ensures blood traceability from donor to recipient; reduces wastage through expiry alerts; supports regulatory audit; automates cross-match documentation. |
| 5 | **Target Users** | Blood Bank Technicians, Lab Technicians, Doctors, Nurses |
| 6 | **Development Priority** | P2 |
| 7 | **Complexity Level** | High |
| 8 | **Estimated Development Effort** | 12–14 developer-weeks |
| 9 | **Required Database Tables** | `clinical.blood_donors`, `clinical.blood_donations`, `clinical.blood_units`, `clinical.blood_inventory`, `clinical.blood_cross_matches`, `clinical.blood_issues`, `clinical.blood_returns`, `clinical.blood_discards`, `clinical.blood_requisitions` |
| 10 | **Required APIs** | `GET/POST /api/v1/blood-donors`, `POST /api/v1/blood-donations`, `GET /api/v1/blood-inventory`, `POST /api/v1/blood-requisitions`, `POST /api/v1/blood-cross-matches`, `POST /api/v1/blood-issues`, `POST /api/v1/blood-returns`, `GET /api/v1/blood-bank/reports/expiry-alerts` |
| 11 | **Required UI Screens** | Donor Registration, Donation Record, Blood Inventory Dashboard, Cross-Match Request, Cross-Match Result, Blood Issue Form, Return/Discard Form, Expiry Alert Report |
| 12 | **RBAC Impact** | New role template: `blood_bank_technician`. Permissions: `bloodbank:read`, `bloodbank:donor_write`, `bloodbank:issue`, `bloodbank:inventory`. Doctors can request (`bloodbank:requisition`). |
| 13 | **Multi-Tenant Considerations** | Blood units tagged with `tenant_id`; no inter-tenant blood sharing in v1; donor IDs unique per tenant. |
| 14 | **Dependencies** | Laboratory Module, Patient Management, IPD/OT (for transfusions), Staff Management |
| 15 | **Revenue Impact** | Medium — niche but high-value for surgical hospitals; +₹2,000–₹5,000/month |
| 16 | **Recommended Subscription Plan** | Enterprise (add-on) |
| 17 | **Future Enhancements** | Regional blood bank network integration, component separation tracking, donor mobile app, NAT testing workflow |

---

### 2.5 Ambulance Management

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | Ambulance & Pre-Hospital Care Management |
| 2 | **Category** | Premium Clinical Module |
| 3 | **Business Problem Solved** | Hospitals with ambulance fleets lack integrated dispatch, trip tracking, and billing for pre-hospital emergency services. |
| 4 | **Business Value** | Optimizes fleet utilization; reduces response times; captures ambulance service revenue; links pre-hospital data to ED admission records. |
| 5 | **Target Users** | Ambulance Dispatchers, Paramedics, ED Staff, Billing Staff |
| 6 | **Development Priority** | P2 |
| 7 | **Complexity Level** | Medium |
| 8 | **Estimated Development Effort** | 8–10 developer-weeks |
| 9 | **Required Database Tables** | `clinical.ambulances`, `clinical.ambulance_crew`, `clinical.ambulance_dispatches`, `clinical.ambulance_trips`, `clinical.pre_hospital_assessments`, `clinical.ambulance_charges` |
| 10 | **Required APIs** | `GET/POST /api/v1/ambulances`, `POST /api/v1/ambulance-dispatches`, `PATCH /api/v1/ambulance-dispatches/{id}/status`, `POST /api/v1/ambulance-trips/{id}/assessment`, `GET /api/v1/ambulance-dispatches/active`, `POST /api/v1/ambulance-trips/{id}/complete`, `POST /api/v1/ambulance-trips/{id}/bill` |
| 11 | **Required UI Screens** | Ambulance Fleet Master, Dispatch Console, Live Trip Tracker, Pre-Hospital Assessment Form, Trip Completion & Billing, Ambulance Utilization Report |
| 12 | **RBAC Impact** | New role: `ambulance_dispatcher`, `paramedic`. Permissions: `ambulance:dispatch`, `ambulance:clinical_write`, `ambulance:read`. |
| 13 | **Multi-Tenant Considerations** | Fleet and dispatch data tenant-isolated; GPS tracking data stored with `tenant_id`; optional location scoping for multi-branch tenants. |
| 14 | **Dependencies** | ED Module (recommended), Patient Management, Billing, Staff Management |
| 15 | **Revenue Impact** | Medium — add-on revenue for hospitals with fleets; +₹2,000–₹4,000/month |
| 16 | **Recommended Subscription Plan** | Enterprise (add-on) |
| 17 | **Future Enhancements** | GPS/telematics integration, patient app booking, inter-facility transfer coordination, 108/emergency helpline integration |

---

### 2.6 Insurance Claims Management

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | Insurance Claims Management |
| 2 | **Category** | Premium Financial Module |
| 3 | **Business Problem Solved** | Hospitals lose 15–25% of insurance revenue due to manual claim preparation, missing documentation, and poor TPA follow-up tracking. |
| 4 | **Business Value** | Accelerates claim submission; reduces rejection rates; improves cash flow from insurance payers; provides claim aging and recovery analytics. |
| 5 | **Target Users** | Billing Staff, Accountants, Hospital Admin, Insurance Desk Staff |
| 6 | **Development Priority** | P1 |
| 7 | **Complexity Level** | High |
| 8 | **Estimated Development Effort** | 14–16 developer-weeks |
| 9 | **Required Database Tables** | `billing.insurance_providers`, `billing.insurance_policies`, `billing.insurance_pre_authorizations`, `billing.insurance_claims`, `billing.claim_line_items`, `billing.claim_documents`, `billing.claim_status_history`, `billing.claim_payments`, `billing.tpa_configurations` |
| 10 | **Required APIs** | `GET/POST /api/v1/insurance-providers`, `POST /api/v1/insurance-pre-auth`, `POST /api/v1/insurance-claims`, `PATCH /api/v1/insurance-claims/{id}/status`, `POST /api/v1/insurance-claims/{id}/documents`, `GET /api/v1/insurance-claims/aging`, `POST /api/v1/insurance-claims/{id}/submit`, `GET /api/v1/insurance-claims/reports` |
| 11 | **Required UI Screens** | Insurance Provider Master, Patient Insurance Details, Pre-Authorization Request, Claim Creation (from IPD/OPD bill), Document Checklist, Claim Submission Tracker, Claim Aging Dashboard, Settlement Recording |
| 12 | **RBAC Impact** | New role: `insurance_desk`. Permissions: `insurance:read`, `insurance:claim_create`, `insurance:claim_submit`, `insurance:settle`. Accountants get full insurance access. |
| 13 | **Multi-Tenant Considerations** | Insurance provider catalog can be system-seeded with tenant overrides; claims strictly `tenant_id` scoped; no cross-tenant claim data. |
| 14 | **Dependencies** | Billing Module, IPD/OPD Modules, Patient Management, Document Management |
| 15 | **Revenue Impact** | Very High — direct revenue recovery for tenants; platform add-on +₹3,000–₹8,000/month |
| 16 | **Recommended Subscription Plan** | Professional (basic tracking) / Enterprise (full claims workflow) |
| 17 | **Future Enhancements** | TPA portal API integration, e-claim (XML/JSON) submission, cashless workflow automation, denial management AI |

---

### 2.7 Vaccination Management

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | Vaccination & Immunization Management |
| 2 | **Category** | Premium Clinical Module |
| 3 | **Business Problem Solved** | Immunization schedules, vaccine inventory (cold chain), and government reporting requirements are poorly tracked in general OPD workflows. |
| 4 | **Business Value** | Ensures immunization schedule compliance; reduces vaccine wastage; supports government immunization program reporting; creates vaccination clinic revenue stream. |
| 5 | **Target Users** | Nurses, Doctors, Pharmacists, Reception Staff |
| 6 | **Development Priority** | P2 |
| 7 | **Complexity Level** | Medium |
| 8 | **Estimated Development Effort** | 6–8 developer-weeks |
| 9 | **Required Database Tables** | `clinical.vaccine_catalog`, `clinical.vaccination_schedules`, `clinical.vaccination_records`, `clinical.vaccination_reminders`, `pharmacy.vaccine_inventory`, `pharmacy.vaccine_batches`, `clinical.immunization_certificates` |
| 10 | **Required APIs** | `GET /api/v1/vaccines`, `GET /api/v1/patients/{id}/vaccination-schedule`, `POST /api/v1/vaccination-records`, `GET /api/v1/vaccination-records`, `POST /api/v1/vaccination-reminders`, `GET /api/v1/vaccine-inventory`, `POST /api/v1/immunization-certificates` |
| 11 | **Required UI Screens** | Vaccine Catalog, Patient Immunization Card, Vaccination Administration Form, Schedule Tracker (due/overdue), Vaccine Inventory, Immunization Certificate Generator, Vaccination Camp Management |
| 12 | **RBAC Impact** | Permissions: `vaccination:read`, `vaccination:administer`, `vaccination:certify`. Nurses and doctors can administer; reception can schedule. |
| 13 | **Multi-Tenant Considerations** | Vaccine catalog system-seeded (national immunization schedule); administration records tenant-scoped; certificates branded per tenant. |
| 14 | **Dependencies** | Patient Management, Pharmacy (vaccine inventory), OPD Module, Notification Module |
| 15 | **Revenue Impact** | Medium — attracts pediatric/wellness clinics; +₹1,500–₹3,000/month |
| 16 | **Recommended Subscription Plan** | Professional (add-on) |
| 17 | **Future Enhancements** | Co-WIN/government registry integration, cold chain temperature monitoring, school vaccination camp module, adverse event reporting |

---

## 3. PHASE 5 – SAAS GROWTH MODULES

**Timeline:** Q2–Q3 2027  
**Theme:** Platform scalability, tenant customization, and SaaS monetization  
**Target:** Support hospital chains, increase ARPU, reduce churn through customization

---

### 3.1 Multi Branch Management

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | Multi-Branch Management |
| 2 | **Category** | SaaS Platform |
| 3 | **Business Problem Solved** | Hospital chains operating multiple facilities cannot manage branches independently while maintaining consolidated reporting and shared patient records. |
| 4 | **Business Value** | Enables chain hospitals as a single tenant; consolidated analytics across branches; shared patient MRN across locations; reduces per-branch licensing friction. |
| 5 | **Target Users** | Hospital Owner, Hospital Admin, Branch Managers, All Staff |
| 6 | **Development Priority** | P1 |
| 7 | **Complexity Level** | High |
| 8 | **Estimated Development Effort** | 10–12 developer-weeks |
| 9 | **Required Database Tables** | `platform.tenant_locations` (enhanced), `platform.branch_settings`, `core.user_branch_assignments`, `clinical.branch_transfers`, `billing.branch_revenue_summary` (materialized view) |
| 10 | **Required APIs** | `GET/POST /api/v1/branches`, `PATCH /api/v1/branches/{id}`, `GET /api/v1/branches/{id}/dashboard`, `POST /api/v1/patients/{id}/branch-transfer`, `GET /api/v1/reports/consolidated`, `POST /api/v1/users/{id}/branch-assignments` |
| 11 | **Required UI Screens** | Branch Master, Branch Selector (global header), Branch Dashboard, Inter-Branch Patient Transfer, Consolidated Reports, Branch User Assignment |
| 12 | **RBAC Impact** | Branch-scoped permissions: `branch:{id}:admin`. Users can be restricted to specific branches. Hospital Owner sees all branches. |
| 13 | **Multi-Tenant Considerations** | Branches are sub-entities within a tenant (not separate tenants); `location_id` added to clinical/billing tables; queries filter by tenant + optional branch. |
| 14 | **Dependencies** | Tenant Management, RBAC (custom roles), Reporting Module |
| 15 | **Revenue Impact** | High — unlocks chain hospital segment; +₹5,000–₹15,000/month per additional branch |
| 16 | **Recommended Subscription Plan** | Enterprise |
| 17 | **Future Enhancements** | Branch-level P&L, centralized procurement, inter-branch inventory transfer, franchise management |

---

### 3.2 White Label Branding

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | White Label Branding |
| 2 | **Category** | SaaS Platform |
| 3 | **Business Problem Solved** | Hospitals want the platform to reflect their brand identity (logo, colors, login page) rather than displaying the SaaS vendor branding. |
| 4 | **Business Value** | Increases tenant satisfaction and perceived ownership; supports reseller/partner channel; reduces churn for brand-conscious hospitals. |
| 5 | **Target Users** | Hospital Owner, Hospital Admin |
| 6 | **Development Priority** | P2 |
| 7 | **Complexity Level** | Medium |
| 8 | **Estimated Development Effort** | 5–7 developer-weeks |
| 9 | **Required Database Tables** | `platform.tenant_branding` (logo_url, favicon_url, primary_color, secondary_color, login_bg_url, custom_css, email_header_logo), `platform.tenant_email_templates` |
| 10 | **Required APIs** | `GET /api/v1/tenant/branding`, `PUT /api/v1/tenant/branding`, `POST /api/v1/tenant/branding/logo` (file upload), `GET /api/v1/public/tenant-branding` (by subdomain, no auth) |
| 11 | **Required UI Screens** | Branding Settings (logo upload, color picker, preview), Login Page Preview, Email Template Customizer, Receipt/Report Header Config |
| 12 | **RBAC Impact** | Permission: `tenant:branding_manage` — restricted to Hospital Owner only. |
| 13 | **Multi-Tenant Considerations** | Branding assets stored in tenant-scoped S3 prefix; CSS variables injected at runtime per subdomain; CDN cache keyed by tenant. |
| 14 | **Dependencies** | Tenant Management, File Storage (S3), Authentication (login page) |
| 15 | **Revenue Impact** | Medium — Enterprise differentiator; +₹2,000–₹5,000/month |
| 16 | **Recommended Subscription Plan** | Enterprise |
| 17 | **Future Enhancements** | Full white-label (remove vendor branding entirely), custom email domain, branded mobile app, partner/reseller portal |

---

### 3.3 Custom Domain Support

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | Custom Domain Support |
| 2 | **Category** | SaaS Platform |
| 3 | **Business Problem Solved** | Enterprise hospitals require access via their own domain (e.g., `hms.apollohospital.com`) instead of `{subdomain}.hmsplatform.com`. |
| 4 | **Business Value** | Professional appearance; meets enterprise IT security policies; enables SSO integration with hospital identity providers. |
| 5 | **Target Users** | Hospital Owner, IT Administrator |
| 6 | **Development Priority** | P2 |
| 7 | **Complexity Level** | Medium |
| 8 | **Estimated Development Effort** | 4–6 developer-weeks |
| 9 | **Required Database Tables** | `platform.tenant_domains` (domain, verification_status, ssl_status, dns_records, verified_at), `platform.domain_verification_logs` |
| 10 | **Required APIs** | `POST /api/v1/tenant/domains`, `GET /api/v1/tenant/domains`, `POST /api/v1/tenant/domains/{id}/verify`, `DELETE /api/v1/tenant/domains/{id}`, `GET /api/v1/tenant/domains/{id}/dns-instructions` |
| 11 | **Required UI Screens** | Custom Domain Setup Wizard, DNS Verification Status, SSL Certificate Status, Domain Management List |
| 12 | **RBAC Impact** | Permission: `tenant:domain_manage` — Hospital Owner only. Platform Admin can override/assist. |
| 13 | **Multi-Tenant Considerations** | Domain-to-tenant mapping in platform layer; TLS cert provisioning per domain (Let's Encrypt/ACM); tenant resolved from Host header, not subdomain only. |
| 14 | **Dependencies** | Tenant Management, Infrastructure (DNS, SSL automation), White Label Branding |
| 15 | **Revenue Impact** | Medium — Enterprise requirement; included in Enterprise plan |
| 16 | **Recommended Subscription Plan** | Enterprise |
| 17 | **Future Enhancements** | Wildcard SSL, multi-domain per tenant, automatic DNS provisioning via Cloudflare API, SSO/SAML with custom domain |

---

### 3.4 Feature Flags

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | Feature Flags & Module Toggles |
| 2 | **Category** | SaaS Platform |
| 3 | **Business Problem Solved** | Platform needs controlled rollout of new features per tenant/plan without code deployments; tenants need ability to enable/disable optional modules. |
| 4 | **Business Value** | Reduces release risk through gradual rollout; enables A/B testing; supports plan-based feature gating; allows beta program management. |
| 5 | **Target Users** | Platform Admin, Hospital Owner, Hospital Admin |
| 6 | **Development Priority** | P1 |
| 7 | **Complexity Level** | Medium |
| 8 | **Estimated Development Effort** | 6–8 developer-weeks |
| 9 | **Required Database Tables** | `platform.feature_flags` (global definitions), `platform.tenant_feature_flags` (overrides), `platform.plan_feature_flags` (plan defaults), `platform.feature_flag_audit_log` |
| 10 | **Required APIs** | `GET /api/v1/feature-flags` (tenant-resolved), `GET/POST /api/v1/admin/feature-flags` (platform), `PUT /api/v1/admin/tenants/{id}/feature-flags`, `GET /api/v1/admin/feature-flags/{key}/rollout-status` |
| 11 | **Required UI Screens** | Platform Admin: Feature Flag Management, Tenant Override Panel, Rollout Dashboard. Tenant Admin: Module Toggle Settings (for optional modules). |
| 12 | **RBAC Impact** | Platform Admin: `platform:feature_flags_manage`. Tenant Owner: `tenant:modules_toggle` (for allowed optional modules only). |
| 13 | **Multi-Tenant Considerations** | Flags evaluated per-request using tenant context; cached in Redis with tenant key; plan defaults applied on tenant provisioning. |
| 14 | **Dependencies** | Tenant Management, Subscription Module, Redis cache |
| 15 | **Revenue Impact** | Indirect — enables safer upsell rollouts and beta programs; reduces churn from buggy releases |
| 16 | **Recommended Subscription Plan** | Platform-level (all plans); module toggles vary by plan |
| 17 | **Future Enhancements** | Percentage-based rollout, user-segment targeting, feature flag analytics, self-service beta enrollment |

---

### 3.5 Advanced Tenant Settings

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | Advanced Tenant Settings |
| 2 | **Category** | SaaS Platform |
| 3 | **Business Problem Solved** | Hospitals have diverse operational configurations (numbering formats, consultation durations, mandatory fields, workflow rules) that basic settings cannot accommodate. |
| 4 | **Business Value** | Reduces support tickets for configuration requests; increases platform adaptability; enables self-service customization without vendor intervention. |
| 5 | **Target Users** | Hospital Admin, Hospital Owner |
| 6 | **Development Priority** | P2 |
| 7 | **Complexity Level** | Medium |
| 8 | **Estimated Development Effort** | 6–8 developer-weeks |
| 9 | **Required Database Tables** | `platform.tenant_settings` (enhanced with typed schema), `platform.tenant_setting_definitions` (system catalog), `platform.tenant_workflow_rules`, `platform.tenant_numbering_sequences` |
| 10 | **Required APIs** | `GET /api/v1/tenant/settings`, `PUT /api/v1/tenant/settings`, `GET /api/v1/tenant/settings/definitions`, `PUT /api/v1/tenant/workflow-rules`, `GET /api/v1/tenant/numbering-sequences`, `PUT /api/v1/tenant/numbering-sequences/{type}` |
| 11 | **Required UI Screens** | Advanced Settings Hub (categorized), Workflow Rules Editor, Numbering Sequence Config, Mandatory Fields Config, Session/Security Settings, Data Retention Settings |
| 12 | **RBAC Impact** | Permission: `tenant:settings_advanced` — Hospital Admin and Owner. Sensitive settings (retention, security) Owner-only. |
| 13 | **Multi-Tenant Considerations** | Settings stored as typed key-value per tenant; validated against system definitions; changes audit-logged; no cross-tenant setting inheritance. |
| 14 | **Dependencies** | Tenant Management, Audit Module |
| 15 | **Revenue Impact** | Low-Medium — reduces support cost; improves Enterprise satisfaction |
| 16 | **Recommended Subscription Plan** | Professional (basic) / Enterprise (full) |
| 17 | **Future Enhancements** | Settings import/export templates, industry preset profiles, branch-level setting overrides, settings change approval workflow |

---

### 3.6 Subscription Analytics

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | Subscription Analytics (Platform Operator) |
| 2 | **Category** | SaaS Platform |
| 3 | **Business Problem Solved** | SaaS operator lacks visibility into MRR, churn, expansion revenue, trial conversion, and plan distribution across the tenant base. |
| 4 | **Business Value** | Enables data-driven pricing decisions; identifies at-risk tenants for proactive retention; tracks growth metrics for investors/board. |
| 5 | **Target Users** | Platform Admin, Product Team, Finance Team |
| 6 | **Development Priority** | P1 |
| 7 | **Complexity Level** | Medium |
| 8 | **Estimated Development Effort** | 6–8 developer-weeks |
| 9 | **Required Database Tables** | `platform.subscription_metrics_daily` (materialized), `platform.tenant_health_scores`, `platform.churn_predictions`, `platform.revenue_events` (expansion, contraction, churn) |
| 10 | **Required APIs** | `GET /api/v1/admin/analytics/mrr`, `GET /api/v1/admin/analytics/churn`, `GET /api/v1/admin/analytics/trial-conversion`, `GET /api/v1/admin/analytics/plan-distribution`, `GET /api/v1/admin/analytics/tenant-health`, `GET /api/v1/admin/analytics/cohort-retention` |
| 11 | **Required UI Screens** | SaaS Metrics Dashboard (MRR, ARR, churn), Trial Conversion Funnel, Plan Distribution Chart, Tenant Health Scoreboard, Cohort Retention Matrix, Revenue Event Timeline |
| 12 | **RBAC Impact** | Platform Admin only: `platform:analytics_read`. No tenant user access. |
| 13 | **Multi-Tenant Considerations** | Aggregated cross-tenant analytics for platform operator only; no tenant sees other tenant metrics; anonymized benchmarks optional (opt-in). |
| 14 | **Dependencies** | Subscription Module, Tenant Management, Billing (platform-level) |
| 15 | **Revenue Impact** | Indirect — improves retention and pricing optimization; estimated 5–10% churn reduction |
| 16 | **Recommended Subscription Plan** | Platform-internal (not tenant-facing) |
| 17 | **Future Enhancements** | Predictive churn ML model, automated dunning optimization, NRR tracking, investor reporting exports |

---

### 3.7 Usage Based Billing

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | Usage-Based Billing |
| 2 | **Category** | SaaS Platform |
| 3 | **Business Problem Solved** | Fixed subscription pricing does not capture value from high-volume tenants or fairly price low-volume clinics; SMS, API calls, and storage need metered billing. |
| 4 | **Business Value** | Increases revenue from high-usage tenants; enables fair pricing for variable workloads; creates expansion revenue beyond base subscription. |
| 5 | **Target Users** | Platform Admin, Hospital Owner, Finance Team |
| 6 | **Development Priority** | P2 |
| 7 | **Complexity Level** | High |
| 8 | **Estimated Development Effort** | 10–12 developer-weeks |
| 9 | **Required Database Tables** | `platform.usage_meters` (definitions), `platform.tenant_usage_records` (daily aggregates), `platform.usage_billing_rules`, `platform.usage_invoices`, `platform.usage_alerts` |
| 10 | **Required APIs** | `GET /api/v1/tenant/usage/current`, `GET /api/v1/tenant/usage/history`, `GET /api/v1/admin/usage/tenants`, `POST /api/v1/admin/usage-billing/generate`, `GET /api/v1/tenant/usage/alerts`, `POST /api/v1/internal/usage/record` (internal meter API) |
| 11 | **Required UI Screens** | Tenant Usage Dashboard, Usage Alert Configuration, Platform Usage Billing Admin, Usage Invoice Detail, Meter Configuration (platform admin) |
| 12 | **RBAC Impact** | Tenant Owner: `tenant:usage_read`. Platform Admin: `platform:usage_billing_manage`. |
| 13 | **Multi-Tenant Considerations** | Usage meters tagged with `tenant_id`; meters include: SMS sent, API calls, storage (GB), active patients, AI invocations; aggregated daily. |
| 14 | **Dependencies** | Subscription Module, Notification Module (SMS metering), API Gateway (call counting), Feature Flags |
| 15 | **Revenue Impact** | High — expansion revenue stream; estimated 10–15% MRR increase from usage charges |
| 16 | **Recommended Subscription Plan** | All plans (metered add-ons); Enterprise (custom usage contracts) |
| 17 | **Future Enhancements** | Real-time usage dashboards, usage-based plan tiers, prepaid usage packs, automated overage billing |

---

## 4. PHASE 6 – PATIENT EXPERIENCE MODULES

**Timeline:** Q3 2027 – Q1 2028  
**Theme:** Patient-facing digital experiences and engagement  
**Target:** Differentiate through patient satisfaction; reduce front-desk load; enable digital-first care

---

### 4.1 Patient Portal

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | Patient Portal (Web) |
| 2 | **Category** | Patient Experience |
| 3 | **Business Problem Solved** | Patients cannot access their health records, bills, lab reports, or prescriptions without visiting the hospital or calling the front desk. |
| 4 | **Business Value** | Reduces front-desk inquiry volume by 40%; improves patient satisfaction; enables 24/7 record access; supports patient empowerment and compliance. |
| 5 | **Target Users** | Patients, Patient Guardians |
| 6 | **Development Priority** | P1 |
| 7 | **Complexity Level** | High |
| 8 | **Estimated Development Effort** | 12–14 developer-weeks |
| 9 | **Required Database Tables** | `core.patient_portal_users`, `core.patient_portal_sessions`, `core.patient_portal_otp`, `core.patient_consent_records`, `core.patient_portal_preferences` |
| 10 | **Required APIs** | `POST /api/v1/portal/auth/otp`, `POST /api/v1/portal/auth/verify`, `GET /api/v1/portal/profile`, `GET /api/v1/portal/appointments`, `GET /api/v1/portal/prescriptions`, `GET /api/v1/portal/lab-reports`, `GET /api/v1/portal/bills`, `GET /api/v1/portal/visits`, `POST /api/v1/portal/consent` |
| 11 | **Required UI Screens** | Portal Login (OTP), Patient Dashboard, My Appointments, My Prescriptions, My Lab Reports, My Bills & Payments, Visit History, Profile & Consent Settings |
| 12 | **RBAC Impact** | New role: `patient_portal_user` (external, not staff). Portal access scoped to own patient records only. No staff RBAC overlap. |
| 13 | **Multi-Tenant Considerations** | Portal resolved by tenant subdomain/domain; patient auth linked to `patient_id` + `tenant_id`; strict IDOR prevention; portal branding per tenant. |
| 14 | **Dependencies** | Patient Management, OPD, Laboratory, Billing, Notification (OTP delivery) |
| 15 | **Revenue Impact** | Medium — retention driver; reduces support cost; +₹1,000–₹3,000/month add-on |
| 16 | **Recommended Subscription Plan** | Professional (add-on) / Enterprise (included) |
| 17 | **Future Enhancements** | Family account linking, health timeline visualization, document upload, appointment self-rescheduling |

---

### 4.2 Doctor Portal

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | Doctor Portal (External Access) |
| 2 | **Category** | Patient Experience |
| 3 | **Business Problem Solved** | Visiting/consulting doctors need remote access to their patient schedules, clinical notes, and earnings without full HMS staff credentials. |
| 4 | **Business Value** | Attracts consulting doctors to the platform; enables remote consultation review; improves doctor engagement and retention. |
| 5 | **Target Users** | Consulting Doctors, Visiting Specialists |
| 6 | **Development Priority** | P2 |
| 7 | **Complexity Level** | Medium |
| 8 | **Estimated Development Effort** | 8–10 developer-weeks |
| 9 | **Required Database Tables** | `core.doctor_portal_preferences`, `clinical.doctor_earnings_summary` (materialized view), `clinical.doctor_schedule_overrides` |
| 10 | **Required APIs** | `GET /api/v1/doctor-portal/schedule`, `GET /api/v1/doctor-portal/patients`, `GET /api/v1/doctor-portal/visits/{id}`, `GET /api/v1/doctor-portal/earnings`, `POST /api/v1/doctor-portal/schedule/override`, `GET /api/v1/doctor-portal/pending-reviews` |
| 11 | **Required UI Screens** | Doctor Login, My Schedule, My Patients (today), Visit Detail (read-only clinical), Earnings Summary, Schedule Override Request |
| 12 | **RBAC Impact** | Subset of `doctor` role permissions: read-only clinical, own schedule, own earnings. No admin or billing access. |
| 13 | **Multi-Tenant Considerations** | Doctor may work across tenants (future); v1 scoped to single tenant per login; earnings data tenant-isolated. |
| 14 | **Dependencies** | Doctor profiles, OPD Module, Billing (doctor fee tracking), Authentication |
| 15 | **Revenue Impact** | Medium — improves doctor satisfaction; indirect retention driver |
| 16 | **Recommended Subscription Plan** | Professional / Enterprise |
| 17 | **Future Enhancements** | Multi-hospital doctor dashboard, telemedicine integration, CME tracking, e-signature for prescriptions |

---

### 4.3 Mobile Application

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | Mobile Application (iOS & Android) |
| 2 | **Category** | Patient Experience |
| 3 | **Business Problem Solved** | Staff and patients need on-the-go access to HMS workflows; web-only limits adoption in clinical settings where desktop access is impractical. |
| 4 | **Business Value** | Increases DAU by 30%; enables bedside workflows for nurses and doctors; patient engagement through push notifications; competitive necessity. |
| 5 | **Target Users** | Doctors, Nurses, Patients, Reception Staff |
| 6 | **Development Priority** | P1 |
| 7 | **Complexity Level** | High |
| 8 | **Estimated Development Effort** | 20–24 developer-weeks (React Native cross-platform) |
| 9 | **Required Database Tables** | `core.mobile_devices` (push tokens), `core.mobile_app_versions`, `core.mobile_sessions`, `comms.push_notification_log` |
| 10 | **Required APIs** | Mobile-optimized versions of core APIs; `POST /api/v1/mobile/register-device`, `GET /api/v1/mobile/config`, `POST /api/v1/mobile/auth/biometric`, `GET /api/v1/mobile/dashboard` (role-based) |
| 11 | **Required UI Screens** | **Staff App:** Dashboard, Patient Search, Today's Appointments, Quick Vitals Entry, Notifications. **Patient App:** Dashboard, Book Appointment, My Reports, My Bills, Profile. |
| 12 | **RBAC Impact** | Same RBAC as web; mobile-specific permissions: `mobile:access` (enabled per role). Biometric auth as convenience layer. |
| 13 | **Multi-Tenant Considerations** | Tenant resolved at login (subdomain/org code); push notifications tagged with `tenant_id`; offline mode caches tenant-scoped data only. |
| 14 | **Dependencies** | All core modules, Patient Portal, Push Notification Service, API v1 stable |
| 15 | **Revenue Impact** | High — major competitive feature; +₹3,000–₹8,000/month; drives patient app engagement |
| 16 | **Recommended Subscription Plan** | Professional (staff app) / Enterprise (staff + patient app) |
| 17 | **Future Enhancements** | Offline mode, wearable integration, in-app chat, QR-based patient check-in |

---

### 4.4 Online Appointment Booking

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | Online Appointment Booking |
| 2 | **Category** | Patient Experience |
| 3 | **Business Problem Solved** | Patients must call or visit the hospital to book appointments, creating phone congestion and limiting booking to business hours. |
| 4 | **Business Value** | Reduces reception call volume by 50%; enables 24/7 booking; fills empty slots through online visibility; attracts new patients via web presence. |
| 5 | **Target Users** | Patients, Reception Staff, Doctors |
| 6 | **Development Priority** | P1 |
| 7 | **Complexity Level** | Medium |
| 8 | **Estimated Development Effort** | 8–10 developer-weeks |
| 9 | **Required Database Tables** | `clinical.online_booking_config`, `clinical.online_appointment_slots`, `clinical.online_booking_requests`, `clinical.online_booking_cancellations` |
| 10 | **Required APIs** | `GET /api/v1/public/doctors` (by subdomain), `GET /api/v1/public/doctors/{id}/slots`, `POST /api/v1/public/appointments/book`, `POST /api/v1/public/appointments/cancel`, `GET /api/v1/portal/appointments`, `PATCH /api/v1/appointments/{id}/confirm` (staff) |
| 11 | **Required UI Screens** | Public Booking Page (tenant-branded), Doctor Selection, Slot Picker Calendar, Booking Confirmation, Booking Management (staff), Online Booking Settings (admin) |
| 12 | **RBAC Impact** | Public endpoints (no auth for browsing); patient auth for booking. Staff: `appointments:online_manage` for confirmation/cancellation. |
| 13 | **Multi-Tenant Considerations** | Public booking page resolved by subdomain; slots scoped to tenant; doctor availability per tenant; no cross-tenant booking. |
| 14 | **Dependencies** | OPD/Appointments Module, Doctor Schedules, Patient Portal, Notification (booking confirmation) |
| 15 | **Revenue Impact** | Medium-High — patient acquisition channel; +₹2,000–₹4,000/month |
| 16 | **Recommended Subscription Plan** | Professional / Enterprise |
| 17 | **Future Enhancements** | Payment at booking, waitlist management, recurring appointments, Google/Practo integration |

---

### 4.5 Telemedicine

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | Telemedicine (Video Consultation) |
| 2 | **Category** | Patient Experience |
| 3 | **Business Problem Solved** | Hospitals cannot offer remote consultations, limiting reach to homebound patients and reducing consultation revenue during disruptions. |
| 4 | **Business Value** | Opens new revenue stream from remote consultations; expands patient catchment area; ensures care continuity during emergencies; competitive differentiator. |
| 5 | **Target Users** | Doctors, Patients, Reception Staff |
| 6 | **Development Priority** | P2 |
| 7 | **Complexity Level** | High |
| 8 | **Estimated Development Effort** | 12–14 developer-weeks |
| 9 | **Required Database Tables** | `clinical.telemedicine_sessions`, `clinical.telemedicine_participants`, `clinical.telemedicine_recordings` (metadata only), `clinical.telemedicine_prescriptions`, `billing.telemedicine_charges` |
| 10 | **Required APIs** | `POST /api/v1/telemedicine/sessions`, `GET /api/v1/telemedicine/sessions/{id}/join-token`, `POST /api/v1/telemedicine/sessions/{id}/end`, `POST /api/v1/telemedicine/sessions/{id}/prescription`, `GET /api/v1/telemedicine/sessions/history`, `POST /api/v1/telemedicine/sessions/{id}/bill` |
| 11 | **Required UI Screens** | Telemedicine Session Lobby, Video Consultation Room, Post-Consultation Notes, Telemedicine Schedule (doctor), Telemedicine Booking (patient), Session History |
| 12 | **RBAC Impact** | Permissions: `telemedicine:conduct` (doctor), `telemedicine:join` (patient), `telemedicine:schedule` (reception). Recording requires explicit consent. |
| 13 | **Multi-Tenant Considerations** | Video sessions scoped to tenant; WebRTC tokens include `tenant_id`; recording storage in tenant S3 prefix; compliance with telemedicine regulations per region. |
| 14 | **Dependencies** | OPD Module, Patient Portal, Billing, WebRTC infrastructure (Twilio/Daily.co), Online Appointment Booking |
| 15 | **Revenue Impact** | High — new revenue stream; +₹3,000–₹6,000/month; per-consultation usage fees |
| 16 | **Recommended Subscription Plan** | Professional (add-on) / Enterprise (included) |
| 17 | **Future Enhancements** | Screen sharing, group consultations, AI transcription, e-pharmacy integration for delivery, insurance coverage for telemedicine |

---

### 4.6 Patient Feedback System

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | Patient Feedback & Satisfaction System |
| 2 | **Category** | Patient Experience |
| 3 | **Business Problem Solved** | Hospitals lack systematic patient satisfaction measurement; feedback is anecdotal and not actionable; negative experiences go unreported until they become complaints. |
| 4 | **Business Value** | Enables NPS tracking per department/doctor; identifies service gaps; supports accreditation requirements (NABH); improves online reputation through proactive resolution. |
| 5 | **Target Users** | Patients, Hospital Admin, Department Heads, Quality Team |
| 6 | **Development Priority** | P2 |
| 7 | **Complexity Level** | Low |
| 8 | **Estimated Development Effort** | 4–6 developer-weeks |
| 9 | **Required Database Tables** | `clinical.feedback_templates`, `clinical.feedback_responses`, `clinical.feedback_questions`, `clinical.feedback_scores`, `clinical.feedback_escalations` |
| 10 | **Required APIs** | `GET /api/v1/feedback/templates`, `POST /api/v1/feedback/responses`, `GET /api/v1/feedback/analytics`, `GET /api/v1/feedback/responses` (admin), `POST /api/v1/feedback/{id}/escalate`, `GET /api/v1/feedback/nps-score` |
| 11 | **Required UI Screens** | Feedback Form (post-visit, patient-facing), Feedback Analytics Dashboard, Department-wise NPS, Doctor Rating Report, Escalation Management, Feedback Template Editor |
| 12 | **RBAC Impact** | Patients submit feedback (no auth or portal auth). Admin: `feedback:read`, `feedback:manage`. Department heads see own department. |
| 13 | **Multi-Tenant Considerations** | Feedback templates customizable per tenant; scores aggregated per tenant; anonymous feedback option; no cross-tenant benchmarking in v1. |
| 14 | **Dependencies** | Patient Portal, OPD/IPD (visit completion trigger), Notification (feedback request SMS/email) |
| 15 | **Revenue Impact** | Low-Medium — retention and quality driver; supports accreditation upsell |
| 16 | **Recommended Subscription Plan** | Professional / Enterprise |
| 17 | **Future Enhancements** | Automated feedback triggers, sentiment analysis (AI), Google Review integration, complaint management workflow |

---

### 4.7 Digital Health Records

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | Digital Health Records (Unified Patient Health Record) |
| 2 | **Category** | Patient Experience |
| 3 | **Business Problem Solved** | Patient health data is fragmented across OPD visits, IPD admissions, lab reports, and prescriptions with no unified longitudinal view. |
| 4 | **Business Value** | Provides complete patient health timeline; reduces duplicate tests; improves clinical decision-making; supports care continuity across departments. |
| 5 | **Target Users** | Doctors, Nurses, Patients (via portal), Hospital Admin |
| 6 | **Development Priority** | P1 |
| 7 | **Complexity Level** | High |
| 8 | **Estimated Development Effort** | 10–12 developer-weeks |
| 9 | **Required Database Tables** | `clinical.patient_health_timeline` (materialized view), `clinical.health_record_documents`, `clinical.health_record_shares` (consent-based), `clinical.health_record_exports` |
| 10 | **Required APIs** | `GET /api/v1/patients/{id}/health-record`, `GET /api/v1/patients/{id}/health-timeline`, `GET /api/v1/patients/{id}/health-record/documents`, `POST /api/v1/patients/{id}/health-record/export`, `POST /api/v1/patients/{id}/health-record/share`, `GET /api/v1/portal/health-record` |
| 11 | **Required UI Screens** | Unified Health Record View (timeline), Document Repository, Health Summary Card, Export/Share Controls, Print-Friendly Health Record |
| 12 | **RBAC Impact** | Doctors/nurses: `health_record:read` (own patients). Patients: portal access to own record. Admin: `health_record:export`. |
| 13 | **Multi-Tenant Considerations** | Health records strictly tenant-scoped; export includes tenant branding; share links are tenant-bound with expiry; FHIR export format (Phase 9 dependency). |
| 14 | **Dependencies** | All clinical modules (OPD, IPD, Lab, Pharmacy), Patient Portal, Document Management |
| 15 | **Revenue Impact** | Medium — clinical value driver; supports Enterprise positioning |
| 16 | **Recommended Subscription Plan** | Enterprise |
| 17 | **Future Enhancements** | ABHA (India) integration, cross-hospital record sharing (with consent), FHIR-compliant export, patient-controlled access logs |

---

## 5. PHASE 7 – AI MODULES

**Timeline:** Q2–Q4 2027  
**Theme:** AI-assisted clinical and operational intelligence  
**Target:** Differentiation, operational efficiency, premium upsell revenue  
**Design Reference:** See AI_FEATURES.md for architecture, human-in-the-loop model, and PHI handling.

---

### 5.1 AI Symptom Analyzer

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | AI Symptom Analyzer |
| 2 | **Category** | AI Clinical |
| 3 | **Business Problem Solved** | Doctors spend significant time on initial differential diagnosis; junior doctors may miss critical symptom patterns. |
| 4 | **Business Value** | Accelerates clinical assessment; suggests differential diagnoses for doctor review; reduces diagnostic errors; improves junior doctor confidence. |
| 5 | **Target Users** | Doctors (OPD, ED) |
| 6 | **Development Priority** | P1 |
| 7 | **Complexity Level** | Medium |
| 8 | **Estimated Development Effort** | 6–8 developer-weeks |
| 9 | **Required Database Tables** | `ai.ai_requests`, `ai.ai_responses`, `ai.symptom_analysis_logs`, `ai.ai_usage_meter` |
| 10 | **Required APIs** | `POST /api/v1/ai/symptom-analyze`, `GET /api/v1/ai/symptom-analyze/{id}`, `POST /api/v1/ai/symptom-analyze/{id}/accept`, `POST /api/v1/ai/symptom-analyze/{id}/reject` |
| 11 | **Required UI Screens** | Symptom Input Panel (within consultation), AI Differential Diagnosis Suggestion, Accept/Modify/Reject Controls, AI Disclaimer Banner |
| 12 | **RBAC Impact** | Permission: `ai:symptom_analyze` — Doctor role only. All AI outputs require doctor approval before saving. |
| 13 | **Multi-Tenant Considerations** | AI requests scoped to `tenant_id`; PHI minimized in prompts; usage metered per tenant; no cross-tenant model training. |
| 14 | **Dependencies** | OPD Module, AI Gateway Service, LLM Provider (OpenAI/Azure), Audit Module |
| 15 | **Revenue Impact** | Medium — AI premium add-on; +₹2,000–₹4,000/month or usage-based |
| 16 | **Recommended Subscription Plan** | Professional (limited) / Enterprise (unlimited) |
| 17 | **Future Enhancements** | Multi-language symptom input, integration with lab results for refined diagnosis, confidence scoring, specialty-specific models |

---

### 5.2 AI Prescription Assistant

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | AI Prescription Assistant |
| 2 | **Category** | AI Clinical |
| 3 | **Business Problem Solved** | Prescription writing is time-consuming; drug interaction and allergy checks are often manual; dosage errors occur with complex regimens. |
| 4 | **Business Value** | Reduces prescription writing time by 40%; auto-checks drug interactions and allergies; suggests evidence-based prescriptions; reduces medication errors. |
| 5 | **Target Users** | Doctors |
| 6 | **Development Priority** | P1 |
| 7 | **Complexity Level** | Medium |
| 8 | **Estimated Development Effort** | 6–8 developer-weeks |
| 9 | **Required Database Tables** | `ai.prescription_suggestions`, `ai.drug_interaction_cache`, `ai.ai_requests`, `ai.ai_usage_meter` |
| 10 | **Required APIs** | `POST /api/v1/ai/prescription-suggest`, `POST /api/v1/ai/prescription-check-interactions`, `POST /api/v1/ai/prescription-suggest/{id}/accept`, `GET /api/v1/ai/prescription-history/{patient_id}` |
| 11 | **Required UI Screens** | AI Prescription Suggest Button (in consultation), Suggested Prescription Review, Interaction Warning Panel, One-Click Accept to E-Prescription |
| 12 | **RBAC Impact** | Permission: `ai:prescription_assist` — Doctor only. AI suggestions never auto-committed; doctor must approve. |
| 13 | **Multi-Tenant Considerations** | Patient allergies and current medications sent as context (tenant-scoped); drug formulary may vary per tenant pharmacy catalog. |
| 14 | **Dependencies** | OPD/IPD Prescriptions, Pharmacy (drug master), Patient Allergies, AI Gateway |
| 15 | **Revenue Impact** | High — high doctor adoption expected; +₹2,000–₹5,000/month |
| 16 | **Recommended Subscription Plan** | Professional+ |
| 17 | **Future Enhancements** | Generic substitution suggestions, pediatric/geriatric dosing, regional formulary compliance, learning from doctor corrections |

---

### 5.3 AI Clinical Notes Generator

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | AI Clinical Notes Generator |
| 2 | **Category** | AI Clinical |
| 3 | **Business Problem Solved** | Doctors spend 30–50% of consultation time on documentation; clinical notes are often incomplete or delayed. |
| 4 | **Business Value** | Reduces documentation time by 50%; improves note completeness; enables doctors to focus on patient interaction; supports billing compliance. |
| 5 | **Target Users** | Doctors, Nurses |
| 6 | **Development Priority** | P1 |
| 7 | **Complexity Level** | Medium |
| 8 | **Estimated Development Effort** | 6–8 developer-weeks |
| 9 | **Required Database Tables** | `ai.clinical_note_drafts`, `ai.ai_requests`, `ai.note_templates`, `ai.ai_usage_meter` |
| 10 | **Required APIs** | `POST /api/v1/ai/clinical-notes/generate`, `GET /api/v1/ai/clinical-notes/{id}`, `POST /api/v1/ai/clinical-notes/{id}/approve`, `PATCH /api/v1/ai/clinical-notes/{id}` (doctor edits) |
| 11 | **Required UI Screens** | Generate Notes Button (post-consultation), AI Draft Review Editor, Approve & Save to Record, Note Template Selector |
| 12 | **RBAC Impact** | Permission: `ai:notes_generate` — Doctor, Nurse (limited). Only licensed clinicians can approve notes. |
| 13 | **Multi-Tenant Considerations** | Visit context (vitals, symptoms, diagnosis) sent to LLM; tenant-specific note templates; all drafts tenant-scoped. |
| 14 | **Dependencies** | OPD/IPD Clinical Notes, AI Gateway, Voice-to-Notes (optional input) |
| 15 | **Revenue Impact** | High — top doctor-requested feature; +₹3,000–₹5,000/month |
| 16 | **Recommended Subscription Plan** | Professional+ |
| 17 | **Future Enhancements** | Specialty-specific templates, ICD-10 code auto-suggestion, multi-language notes, structured + narrative dual output |

---

### 5.4 AI Discharge Summary Generator

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | AI Discharge Summary Generator |
| 2 | **Category** | AI Clinical |
| 3 | **Business Problem Solved** | Discharge summaries are time-consuming to compile from scattered IPD data; delays discharge and reduces bed turnover. |
| 4 | **Business Value** | Reduces discharge summary preparation from 30 min to 5 min; accelerates bed turnover; improves summary completeness for continuity of care. |
| 5 | **Target Users** | Doctors (IPD) |
| 6 | **Development Priority** | P2 |
| 7 | **Complexity Level** | Medium |
| 8 | **Estimated Development Effort** | 5–7 developer-weeks |
| 9 | **Required Database Tables** | `ai.discharge_summary_drafts`, `ai.ai_requests`, `ai.ai_usage_meter` |
| 10 | **Required APIs** | `POST /api/v1/ai/discharge-summary/generate`, `GET /api/v1/ai/discharge-summary/{id}`, `POST /api/v1/ai/discharge-summary/{id}/approve`, `POST /api/v1/admissions/{id}/discharge` (with approved summary) |
| 11 | **Required UI Screens** | Generate Discharge Summary Button, AI Draft Review (admission → discharge timeline), Edit & Approve, Final Discharge Summary Preview |
| 12 | **RBAC Impact** | Permission: `ai:discharge_summary` — Doctor only. Discharge requires approved summary. |
| 13 | **Multi-Tenant Considerations** | Aggregates IPD data (vitals, notes, medications, procedures) from tenant-scoped records; summary branded per tenant. |
| 14 | **Dependencies** | IPD Module (admissions, nursing notes, vitals, medications), AI Gateway |
| 15 | **Revenue Impact** | Medium — IPD-heavy hospitals; +₹2,000–₹3,000/month |
| 16 | **Recommended Subscription Plan** | Professional (IPD tenants) / Enterprise |
| 17 | **Future Enhancements** | Follow-up plan generation, medication reconciliation, patient-friendly summary version, fax/email to referring physician |

---

### 5.5 AI Medical Report Summarizer

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | AI Medical Report Summarizer |
| 2 | **Category** | AI Clinical |
| 3 | **Business Problem Solved** | Doctors struggle to quickly interpret lengthy lab reports and radiology reports; critical abnormalities may be buried in data. |
| 4 | **Business Value** | Highlights critical/abnormal findings instantly; reduces report review time by 60%; improves clinical response to abnormal results. |
| 5 | **Target Users** | Doctors, Lab Technicians |
| 6 | **Development Priority** | P2 |
| 7 | **Complexity Level** | Medium |
| 8 | **Estimated Development Effort** | 5–7 developer-weeks |
| 9 | **Required Database Tables** | `ai.report_summaries`, `ai.ai_requests`, `ai.ai_usage_meter` |
| 10 | **Required APIs** | `POST /api/v1/ai/reports/summarize`, `GET /api/v1/ai/reports/summarize/{id}`, `POST /api/v1/ai/reports/summarize/{id}/acknowledge` |
| 11 | **Required UI Screens** | AI Summary Tab (on lab/radiology report), Abnormal Highlights Panel, Trend Comparison View, Acknowledge Summary |
| 12 | **RBAC Impact** | Permission: `ai:report_summarize` — Doctor, Lab Technician. |
| 13 | **Multi-Tenant Considerations** | Report data sent to LLM is tenant-scoped; historical results for trend context from same tenant only. |
| 14 | **Dependencies** | Laboratory Module, Radiology (future), AI Gateway |
| 15 | **Revenue Impact** | Medium — +₹1,500–₹3,000/month |
| 16 | **Recommended Subscription Plan** | Professional+ |
| 17 | **Future Enhancements** | Multi-report correlation, critical value auto-alert, patient-friendly summary, comparison with reference ranges by age/gender |

---

### 5.6 AI Voice To Clinical Notes

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | AI Voice-to-Clinical Notes |
| 2 | **Category** | AI Clinical |
| 3 | **Business Problem Solved** | Doctors prefer speaking to typing; manual transcription is slow and interrupts patient interaction. |
| 4 | **Business Value** | Enables hands-free documentation during consultation; reduces note-taking time by 70%; improves doctor-patient engagement. |
| 5 | **Target Users** | Doctors, Nurses |
| 6 | **Development Priority** | P2 |
| 7 | **Complexity Level** | High |
| 8 | **Estimated Development Effort** | 10–12 developer-weeks |
| 9 | **Required Database Tables** | `ai.voice_recordings` (metadata), `ai.voice_transcriptions`, `ai.clinical_note_drafts`, `ai.ai_requests`, `ai.ai_usage_meter` |
| 10 | **Required APIs** | `POST /api/v1/ai/voice/upload`, `POST /api/v1/ai/voice/transcribe`, `POST /api/v1/ai/voice/{id}/generate-notes`, `GET /api/v1/ai/voice/{id}/status`, `POST /api/v1/ai/voice/{id}/approve` |
| 11 | **Required UI Screens** | Voice Record Button (in consultation), Recording Indicator, Transcription Review, AI Notes Draft from Voice, Approve & Save |
| 12 | **RBAC Impact** | Permission: `ai:voice_notes` — Doctor, Nurse. Audio stored in tenant-scoped S3; auto-deleted per retention policy. |
| 13 | **Multi-Tenant Considerations** | Audio files in tenant S3 prefix; transcription processed with tenant context; medical vocabulary per specialty; PHI in audio handled per compliance. |
| 14 | **Dependencies** | AI Gateway, Speech-to-Text (Whisper/Azure), Clinical Notes Generator, S3 Storage |
| 15 | **Revenue Impact** | High — premium AI feature; +₹3,000–₹6,000/month |
| 16 | **Recommended Subscription Plan** | Enterprise |
| 17 | **Future Enhancements** | Real-time streaming transcription, multi-speaker detection (doctor/patient), regional language support, ambient clinical intelligence |

---

### 5.7 AI Revenue Analytics

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | AI Revenue Analytics |
| 2 | **Category** | AI Operational |
| 3 | **Business Problem Solved** | Hospital administrators cannot easily identify revenue leakage, unbilled services, or pricing optimization opportunities from raw billing data. |
| 4 | **Business Value** | Identifies average ₹10,000–₹50,000/month in revenue leakage per hospital; suggests pricing optimizations; forecasts revenue trends. |
| 5 | **Target Users** | Hospital Owner, Accountants, Hospital Admin |
| 6 | **Development Priority** | P1 |
| 7 | **Complexity Level** | Medium |
| 8 | **Estimated Development Effort** | 8–10 developer-weeks |
| 9 | **Required Database Tables** | `ai.revenue_anomalies`, `ai.revenue_forecasts`, `ai.revenue_insights`, `ai.ai_usage_meter` |
| 10 | **Required APIs** | `GET /api/v1/ai/revenue/insights`, `GET /api/v1/ai/revenue/leakage-report`, `GET /api/v1/ai/revenue/forecast`, `POST /api/v1/ai/revenue/analyze`, `GET /api/v1/ai/revenue/anomalies` |
| 11 | **Required UI Screens** | AI Revenue Insights Dashboard, Leakage Detection Report, Revenue Forecast Chart, Anomaly Alerts, Recommended Actions Panel |
| 12 | **RBAC Impact** | Permission: `ai:revenue_analytics` — Hospital Owner, Accountant. No clinical staff access. |
| 13 | **Multi-Tenant Considerations** | Analysis runs on tenant's own billing data only; benchmarks (if shown) use anonymized cross-tenant aggregates (opt-in). |
| 14 | **Dependencies** | Billing Module, Reporting Module, AI Gateway |
| 15 | **Revenue Impact** | Very High — direct ROI for tenants; strong upsell driver; +₹3,000–₹8,000/month |
| 16 | **Recommended Subscription Plan** | Enterprise |
| 17 | **Future Enhancements** | Automated billing correction suggestions, payer mix optimization, department profitability AI, cash flow forecasting |

---

### 5.8 AI Inventory Forecasting

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | AI Inventory Forecasting |
| 2 | **Category** | AI Operational |
| 3 | **Business Problem Solved** | Pharmacy and supply stockouts disrupt patient care; overstocking ties up capital; manual reorder points are inaccurate. |
| 4 | **Business Value** | Reduces stockouts by 40%; optimizes inventory carrying cost; automates reorder suggestions; predicts seasonal demand patterns. |
| 5 | **Target Users** | Pharmacists, Hospital Admin, Inventory Managers |
| 6 | **Development Priority** | P2 |
| 7 | **Complexity Level** | Medium |
| 8 | **Estimated Development Effort** | 6–8 developer-weeks |
| 9 | **Required Database Tables** | `ai.inventory_forecasts`, `ai.reorder_suggestions`, `ai.demand_patterns`, `ai.ai_usage_meter` |
| 10 | **Required APIs** | `GET /api/v1/ai/inventory/forecast`, `GET /api/v1/ai/inventory/reorder-suggestions`, `POST /api/v1/ai/inventory/analyze`, `GET /api/v1/ai/inventory/stockout-risk` |
| 11 | **Required UI Screens** | Inventory Forecast Dashboard, Reorder Suggestions List, Stockout Risk Alerts, Demand Trend Charts, One-Click Purchase Order Draft |
| 12 | **RBAC Impact** | Permission: `ai:inventory_forecast` — Pharmacist, Hospital Admin. |
| 13 | **Multi-Tenant Considerations** | Forecasts based on tenant's own dispensing patterns; no cross-tenant demand data sharing. |
| 14 | **Dependencies** | Pharmacy Module, Inventory Management, AI Gateway |
| 15 | **Revenue Impact** | Medium — cost savings for tenants; +₹1,500–₹3,000/month |
| 16 | **Recommended Subscription Plan** | Professional (pharmacy tenants) / Enterprise |
| 17 | **Future Enhancements** | Supplier lead time integration, expiry-aware ordering, multi-location inventory optimization, automated PO generation |

---

### 5.9 AI Follow-Up Assistant

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | AI Follow-Up Assistant |
| 2 | **Category** | AI Operational |
| 3 | **Business Problem Solved** | Post-discharge and post-consultation follow-ups are inconsistently managed; patients are lost to follow-up, reducing care quality and revenue. |
| 4 | **Business Value** | Automates follow-up scheduling based on diagnosis; sends personalized reminders; tracks follow-up compliance; increases return visit revenue. |
| 5 | **Target Users** | Doctors, Nurses, Reception Staff, Patients |
| 6 | **Development Priority** | P2 |
| 7 | **Complexity Level** | Medium |
| 8 | **Estimated Development Effort** | 6–8 developer-weeks |
| 9 | **Required Database Tables** | `ai.follow_up_plans`, `ai.follow_up_tasks`, `ai.follow_up_reminders`, `ai.ai_usage_meter` |
| 10 | **Required APIs** | `POST /api/v1/ai/follow-up/generate`, `GET /api/v1/ai/follow-up/plans`, `PATCH /api/v1/ai/follow-up/tasks/{id}`, `GET /api/v1/ai/follow-up/compliance-report`, `POST /api/v1/ai/follow-up/send-reminder` |
| 11 | **Required UI Screens** | AI Follow-Up Plan Generator (post-consultation), Follow-Up Task List, Compliance Dashboard, Patient Reminder Preview, Follow-Up Outcome Recording |
| 12 | **RBAC Impact** | Permissions: `ai:follow_up_manage` (staff), `ai:follow_up_view` (doctor). Patients receive reminders via portal/SMS. |
| 13 | **Multi-Tenant Considerations** | Follow-up rules customizable per tenant specialty; reminders branded per tenant; SMS usage metered. |
| 14 | **Dependencies** | OPD/IPD Modules, Notification Module, AI Gateway, Online Appointment Booking |
| 15 | **Revenue Impact** | Medium — increases return visits; +₹1,500–₹3,000/month |
| 16 | **Recommended Subscription Plan** | Professional+ |
| 17 | **Future Enhancements** | Chronic disease management protocols, medication adherence tracking, automated outcome surveys, care pathway templates |

---

### 5.10 AI Chat Assistant

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | AI Chat Assistant (In-App) |
| 2 | **Category** | AI Platform |
| 3 | **Business Problem Solved** | Staff struggle to learn HMS workflows; support tickets for "how do I..." are high; onboarding new staff is slow. |
| 4 | **Business Value** | Reduces support tickets by 30%; accelerates staff onboarding; provides instant workflow guidance; improves feature discovery and adoption. |
| 5 | **Target Users** | All Staff Roles, Hospital Admin |
| 6 | **Development Priority** | P3 |
| 7 | **Complexity Level** | Medium |
| 8 | **Estimated Development Effort** | 6–8 developer-weeks |
| 9 | **Required Database Tables** | `ai.chat_sessions`, `ai.chat_messages`, `ai.knowledge_base_articles`, `ai.chat_feedback`, `ai.ai_usage_meter` |
| 10 | **Required APIs** | `POST /api/v1/ai/chat/sessions`, `POST /api/v1/ai/chat/messages`, `GET /api/v1/ai/chat/sessions/{id}/history`, `POST /api/v1/ai/chat/feedback`, `GET /api/v1/admin/ai/knowledge-base` |
| 11 | **Required UI Screens** | Chat Widget (floating, all pages), Conversation History, Suggested Actions (deep links), Feedback Rating, Knowledge Base Admin (platform) |
| 12 | **RBAC Impact** | Permission: `ai:chat_assistant` — all staff roles. Chat responses respect user's RBAC (won't reveal unauthorized data). |
| 13 | **Multi-Tenant Considerations** | Chat context includes tenant module configuration; knowledge base is platform-wide + tenant-specific articles; no clinical data accessed by chat. |
| 14 | **Dependencies** | AI Gateway, Knowledge Base, All core modules (for context-aware help) |
| 15 | **Revenue Impact** | Low-Medium — reduces support cost; improves retention; included as platform value-add |
| 16 | **Recommended Subscription Plan** | All plans (basic) / Enterprise (advanced with custom knowledge base) |
| 17 | **Future Enhancements** | Voice chat, multilingual support, patient-facing chatbot, integration with support ticketing |

---

## 6. PHASE 8 – ENTERPRISE MODULES

**Timeline:** Q4 2027 – Q2 2028  
**Theme:** Enterprise-grade analytics, compliance, and workforce management  
**Target:** Large hospitals, hospital chains, and regulated healthcare organizations

---

### 6.1 Executive Analytics Dashboard

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | Executive Analytics Dashboard |
| 2 | **Category** | Enterprise Analytics |
| 3 | **Business Problem Solved** | Hospital leadership lacks real-time visibility into KPIs across clinical, operational, and financial dimensions in a single view. |
| 4 | **Business Value** | Enables data-driven strategic decisions; identifies underperforming departments; tracks growth metrics; supports board reporting. |
| 5 | **Target Users** | Hospital Owner, CMO, Hospital Admin, Department Heads |
| 6 | **Development Priority** | P1 |
| 7 | **Complexity Level** | High |
| 8 | **Estimated Development Effort** | 10–12 developer-weeks |
| 9 | **Required Database Tables** | `analytics.kpi_definitions`, `analytics.kpi_snapshots_daily`, `analytics.dashboard_configs`, `analytics.dashboard_widgets`, `analytics.department_metrics` |
| 10 | **Required APIs** | `GET /api/v1/analytics/executive-dashboard`, `GET /api/v1/analytics/kpis`, `GET /api/v1/analytics/department-comparison`, `GET /api/v1/analytics/trends`, `PUT /api/v1/analytics/dashboard-config`, `GET /api/v1/analytics/export` |
| 11 | **Required UI Screens** | Executive Dashboard (KPI cards, charts), Department Comparison View, Trend Analysis, Custom Dashboard Builder, Scheduled Report Export |
| 12 | **RBAC Impact** | Permission: `analytics:executive` — Owner, Admin. Department heads see own department via `analytics:department`. |
| 13 | **Multi-Tenant Considerations** | All metrics computed per tenant; dashboard configs per tenant; branch-level drill-down for multi-branch tenants. |
| 14 | **Dependencies** | All clinical and billing modules, Reporting Module, Multi-Branch (optional) |
| 15 | **Revenue Impact** | High — Enterprise retention driver; +₹5,000–₹10,000/month |
| 16 | **Recommended Subscription Plan** | Enterprise |
| 17 | **Future Enhancements** | AI-powered insights, benchmark against anonymized peer data, mobile executive app, board presentation mode |

---

### 6.2 Corporate Health Packages

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | Corporate Health Packages |
| 2 | **Category** | Enterprise Revenue |
| 3 | **Business Problem Solved** | Hospitals offering corporate health checkup packages lack digital management for corporate accounts, employee enrollment, and package billing. |
| 4 | **Business Value** | Opens B2B revenue stream; automates corporate health camp management; simplifies bulk billing; tracks package utilization. |
| 5 | **Target Users** | Hospital Admin, Billing Staff, Corporate HR, Reception Staff |
| 6 | **Development Priority** | P2 |
| 7 | **Complexity Level** | Medium |
| 8 | **Estimated Development Effort** | 8–10 developer-weeks |
| 9 | **Required Database Tables** | `billing.corporate_accounts`, `billing.corporate_contracts`, `billing.health_packages`, `billing.package_items`, `billing.corporate_enrollments`, `billing.corporate_invoices` |
| 10 | **Required APIs** | `GET/POST /api/v1/corporate-accounts`, `GET/POST /api/v1/health-packages`, `POST /api/v1/corporate-enrollments`, `GET /api/v1/corporate-accounts/{id}/utilization`, `POST /api/v1/corporate-invoices`, `GET /api/v1/corporate-accounts/{id}/employees` |
| 11 | **Required UI Screens** | Corporate Account Master, Health Package Builder, Employee Enrollment, Camp Schedule Manager, Utilization Dashboard, Corporate Invoice Generator |
| 12 | **RBAC Impact** | Permissions: `corporate:manage` (admin), `corporate:bill` (accountant), `corporate:enroll` (reception). |
| 13 | **Multi-Tenant Considerations** | Corporate accounts and packages tenant-scoped; employee data linked to patient records within tenant. |
| 14 | **Dependencies** | Billing Module, Laboratory, Patient Management, OPD |
| 15 | **Revenue Impact** | Medium — enables B2B revenue for tenants; platform add-on +₹2,000–₹5,000/month |
| 16 | **Recommended Subscription Plan** | Enterprise |
| 17 | **Future Enhancements** | Corporate portal for HR, automated camp scheduling, insurance integration for corporate policies, wellness program tracking |

---

### 6.3 HR & Payroll

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | HR & Payroll Management |
| 2 | **Category** | Enterprise Operations |
| 3 | **Business Problem Solved** | Hospitals manage staff attendance, leave, and payroll in separate systems disconnected from the HMS staff records. |
| 4 | **Business Value** | Unified staff lifecycle management; reduces HR administrative overhead; integrates doctor fee calculations with payroll; compliance with labor laws. |
| 5 | **Target Users** | HR Manager, Hospital Admin, Hospital Owner, Staff |
| 6 | **Development Priority** | P2 |
| 7 | **Complexity Level** | High |
| 8 | **Estimated Development Effort** | 14–16 developer-weeks |
| 9 | **Required Database Tables** | `hr.attendance_records`, `hr.leave_types`, `hr.leave_requests`, `hr.leave_balances`, `hr.payroll_runs`, `hr.payroll_items`, `hr.salary_structures`, `hr.tax_deductions`, `hr.payslips` |
| 10 | **Required APIs** | `POST /api/v1/hr/attendance/check-in`, `GET /api/v1/hr/attendance`, `POST /api/v1/hr/leave-requests`, `PATCH /api/v1/hr/leave-requests/{id}/approve`, `POST /api/v1/hr/payroll/generate`, `GET /api/v1/hr/payslips`, `GET /api/v1/hr/leave-balances` |
| 11 | **Required UI Screens** | Attendance Dashboard, Leave Request & Approval, Payroll Generation, Payslip Viewer, Salary Structure Config, Leave Balance Report, HR Analytics |
| 12 | **RBAC Impact** | New role: `hr_manager`. Permissions: `hr:attendance`, `hr:leave_approve`, `hr:payroll_manage`, `hr:payslip_view` (own). |
| 13 | **Multi-Tenant Considerations** | HR data strictly tenant-scoped; payroll rules configurable per tenant region; staff linked to existing `core.staff` records. |
| 14 | **Dependencies** | Staff Management, Billing (doctor fees), Department Management |
| 15 | **Revenue Impact** | Medium — reduces need for separate HR software; +₹3,000–₹6,000/month |
| 16 | **Recommended Subscription Plan** | Enterprise |
| 17 | **Future Enhancements** | Biometric attendance integration, shift scheduling, performance reviews, statutory compliance reports (PF, ESI) |

---

### 6.4 Compliance Management

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | Compliance Management |
| 2 | **Category** | Enterprise Compliance |
| 3 | **Business Problem Solved** | Hospitals face accreditation (NABH, JCI) and regulatory audits without systematic compliance tracking, policy management, or evidence collection. |
| 4 | **Business Value** | Streamlines accreditation preparation; tracks compliance tasks and deadlines; maintains policy repository; reduces audit preparation time by 50%. |
| 5 | **Target Users** | Quality Manager, Hospital Admin, Hospital Owner, Department Heads |
| 6 | **Development Priority** | P2 |
| 7 | **Complexity Level** | Medium |
| 8 | **Estimated Development Effort** | 8–10 developer-weeks |
| 9 | **Required Database Tables** | `compliance.standards_catalog`, `compliance.compliance_tasks`, `compliance.policy_documents`, `compliance.compliance_evidence`, `compliance.compliance_audits`, `compliance.corrective_actions` |
| 10 | **Required APIs** | `GET /api/v1/compliance/standards`, `GET/POST /api/v1/compliance/tasks`, `POST /api/v1/compliance/evidence`, `GET /api/v1/compliance/dashboard`, `POST /api/v1/compliance/audits`, `GET /api/v1/compliance/policies` |
| 11 | **Required UI Screens** | Compliance Dashboard (score, overdue tasks), Standards Checklist, Policy Repository, Evidence Upload, Audit Schedule, Corrective Action Tracker |
| 12 | **RBAC Impact** | New role: `quality_manager`. Permissions: `compliance:manage`, `compliance:evidence_upload`, `compliance:audit`. |
| 13 | **Multi-Tenant Considerations** | Standards catalog system-seeded (NABH, JCI); compliance tasks and evidence tenant-scoped; policies per tenant. |
| 14 | **Dependencies** | Audit Module, Document Management, Staff Management |
| 15 | **Revenue Impact** | Medium — accreditation-focused hospitals; +₹2,000–₹5,000/month |
| 16 | **Recommended Subscription Plan** | Enterprise |
| 17 | **Future Enhancements** | Automated evidence collection from HMS data, accreditation body integration, compliance scoring AI, regulatory update alerts |

---

### 6.5 Audit Management

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | Advanced Audit Management |
| 2 | **Category** | Enterprise Compliance |
| 3 | **Business Problem Solved** | Basic audit logs are insufficient for forensic investigation, compliance reporting, and anomaly detection across clinical and financial operations. |
| 4 | **Business Value** | Provides forensic-grade audit trail; enables compliance reporting; detects suspicious access patterns; supports regulatory investigations. |
| 5 | **Target Users** | Hospital Owner, Quality Manager, Platform Admin, Compliance Officers |
| 6 | **Development Priority** | P2 |
| 7 | **Complexity Level** | Medium |
| 8 | **Estimated Development Effort** | 6–8 developer-weeks |
| 9 | **Required Database Tables** | `audit.audit_logs` (enhanced), `audit.audit_log_exports`, `audit.access_anomaly_alerts`, `audit.audit_retention_policies`, `audit.audit_search_index` |
| 10 | **Required APIs** | `GET /api/v1/audit/logs` (advanced filters), `GET /api/v1/audit/logs/{id}`, `POST /api/v1/audit/export`, `GET /api/v1/audit/anomalies`, `GET /api/v1/audit/user-activity/{user_id}`, `GET /api/v1/audit/patient-access/{patient_id}` |
| 11 | **Required UI Screens** | Audit Log Explorer (advanced search), User Activity Timeline, Patient Record Access Log, Anomaly Alerts, Audit Export Wizard, Retention Policy Config |
| 12 | **RBAC Impact** | Permission: `audit:read` — Owner, Quality Manager. `audit:export` — Owner only. Platform Admin has cross-tenant audit (metadata only). |
| 13 | **Multi-Tenant Considerations** | Audit logs immutable and tenant-scoped; retention policies per tenant; export includes tenant branding for regulatory submission. |
| 14 | **Dependencies** | Existing Audit Module (MVP), RBAC, All clinical/financial modules |
| 15 | **Revenue Impact** | Medium — compliance requirement for Enterprise; included in Enterprise plan |
| 16 | **Recommended Subscription Plan** | Enterprise |
| 17 | **Future Enhancements** | Real-time anomaly detection (AI), blockchain audit trail, automated compliance reports, SIEM integration |

---

### 6.6 Data Warehouse Integration

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | Data Warehouse Integration |
| 2 | **Category** | Enterprise Analytics |
| 3 | **Business Problem Solved** | Enterprise hospitals need to combine HMS data with other business systems (ERP, CRM) in a data warehouse for advanced analytics and BI. |
| 4 | **Business Value** | Enables enterprise BI tools (Power BI, Tableau); supports custom analytics beyond built-in dashboards; data-driven hospital management. |
| 5 | **Target Users** | Hospital IT, Data Analysts, Hospital Owner, Platform Admin |
| 6 | **Development Priority** | P3 |
| 7 | **Complexity Level** | High |
| 8 | **Estimated Development Effort** | 12–14 developer-weeks |
| 9 | **Required Database Tables** | `analytics.etl_jobs`, `analytics.etl_job_runs`, `analytics.data_export_configs`, `analytics.warehouse_connections`, `analytics.etl_watermarks` |
| 10 | **Required APIs** | `GET/POST /api/v1/analytics/etl-jobs`, `POST /api/v1/analytics/etl-jobs/{id}/run`, `GET /api/v1/analytics/etl-jobs/{id}/status`, `GET/POST /api/v1/analytics/warehouse-connections`, `GET /api/v1/analytics/data-dictionary` |
| 11 | **Required UI Screens** | ETL Job Configuration, Warehouse Connection Setup, Job Run Monitor, Data Dictionary Browser, Export Schedule Manager |
| 12 | **RBAC Impact** | Permission: `analytics:warehouse_manage` — Hospital IT, Owner. Platform Admin manages infrastructure. |
| 13 | **Multi-Tenant Considerations** | ETL exports tenant-scoped data only; warehouse connections per tenant; scheduled incremental exports with `tenant_id` partitioning. |
| 14 | **Dependencies** | All modules (data sources), Executive Analytics, API v1 |
| 15 | **Revenue Impact** | Medium — Enterprise requirement; +₹5,000–₹10,000/month |
| 16 | **Recommended Subscription Plan** | Enterprise (custom) |
| 17 | **Future Enhancements** | Real-time CDC streaming, pre-built BI templates, data lake integration, anonymized research data exports |

---

### 6.7 Business Intelligence Reports

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | Business Intelligence Reports |
| 2 | **Category** | Enterprise Analytics |
| 3 | **Business Problem Solved** | Built-in reports do not meet all hospital reporting needs; custom report creation requires vendor support or external tools. |
| 4 | **Business Value** | Empowers hospitals to create custom reports without vendor dependency; schedules automated report delivery; supports regulatory reporting requirements. |
| 5 | **Target Users** | Hospital Admin, Accountants, Department Heads, Quality Manager |
| 6 | **Development Priority** | P2 |
| 7 | **Complexity Level** | High |
| 8 | **Estimated Development Effort** | 10–12 developer-weeks |
| 9 | **Required Database Tables** | `analytics.report_definitions`, `analytics.report_schedules`, `analytics.report_executions`, `analytics.report_templates`, `analytics.report_shares` |
| 10 | **Required APIs** | `GET/POST /api/v1/reports/definitions`, `POST /api/v1/reports/execute`, `GET /api/v1/reports/executions/{id}`, `GET/POST /api/v1/reports/schedules`, `GET /api/v1/reports/templates`, `POST /api/v1/reports/export` |
| 11 | **Required UI Screens** | Report Builder (drag-and-drop), Report Template Gallery, Report Viewer, Schedule Configuration, Report Sharing, Execution History |
| 12 | **RBAC Impact** | Permissions: `reports:create`, `reports:execute`, `reports:schedule`, `reports:share`. Department-scoped report access. |
| 13 | **Multi-Tenant Considerations** | Report definitions tenant-scoped; templates can be system-seeded; execution results contain only tenant data; scheduled delivery to tenant users only. |
| 14 | **Dependencies** | Reporting Module (MVP basic reports), Executive Analytics, All data modules |
| 15 | **Revenue Impact** | Medium-High — reduces external BI tool need; +₹3,000–₹6,000/month |
| 16 | **Recommended Subscription Plan** | Professional (basic builder) / Enterprise (full BI) |
| 17 | **Future Enhancements** | AI report generation from natural language, cross-module correlation reports, regulatory report templates, embedded analytics |

---

## 7. PHASE 9 – INTEGRATIONS

**Timeline:** Q1 2028 – Q4 2028  
**Theme:** External system connectivity and healthcare interoperability  
**Target:** Ecosystem expansion, enterprise requirements, market differentiation

---

### 7.1 WhatsApp Integration

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | WhatsApp Business Integration |
| 2 | **Category** | Communication Integration |
| 3 | **Business Problem Solved** | Patients prefer WhatsApp for appointment reminders, report delivery, and communication; hospitals lack integrated WhatsApp messaging. |
| 4 | **Business Value** | 98% message open rate vs. 20% email; reduces no-shows; enables report delivery on preferred channel; improves patient engagement. |
| 5 | **Target Users** | Patients, Reception Staff, Hospital Admin |
| 6 | **Development Priority** | P1 |
| 7 | **Complexity Level** | Medium |
| 8 | **Estimated Development Effort** | 6–8 developer-weeks |
| 9 | **Required Database Tables** | `comms.whatsapp_configs`, `comms.whatsapp_templates`, `comms.whatsapp_messages`, `comms.whatsapp_delivery_log` |
| 10 | **Required APIs** | `POST /api/v1/integrations/whatsapp/send`, `GET /api/v1/integrations/whatsapp/templates`, `POST /api/v1/integrations/whatsapp/webhook`, `GET /api/v1/integrations/whatsapp/status`, `PUT /api/v1/tenant/integrations/whatsapp/config` |
| 11 | **Required UI Screens** | WhatsApp Configuration (admin), Message Template Manager, Delivery Log, Test Message Sender, WhatsApp Analytics |
| 12 | **RBAC Impact** | Permission: `integrations:whatsapp_manage` (admin). Automated messages via system; manual send via `comms:send`. |
| 13 | **Multi-Tenant Considerations** | WhatsApp Business API account per tenant (or shared with tenant routing); templates approved per tenant; message logs tenant-scoped. |
| 14 | **Dependencies** | Notification Module, Patient Management, Appointment Module |
| 15 | **Revenue Impact** | Medium — usage-based messaging revenue; +₹1,000–₹3,000/month + per-message fees |
| 16 | **Recommended Subscription Plan** | Professional (add-on) / Enterprise (included quota) |
| 17 | **Future Enhancements** | Two-way chat, appointment booking via WhatsApp, payment links, chatbot for FAQs |

---

### 7.2 SMS Integration

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | SMS Gateway Integration |
| 2 | **Category** | Communication Integration |
| 3 | **Business Problem Solved** | Hospitals need reliable SMS delivery for OTPs, appointment reminders, and critical alerts; basic SMS in MVP needs enterprise-grade gateway. |
| 4 | **Business Value** | Reliable message delivery with tracking; DLT compliance (India); delivery reports; reduces no-shows by 25%. |
| 5 | **Target Users** | All Staff (automated), Hospital Admin |
| 6 | **Development Priority** | P1 |
| 7 | **Complexity Level** | Low |
| 8 | **Estimated Development Effort** | 3–4 developer-weeks |
| 9 | **Required Database Tables** | `comms.sms_configs`, `comms.sms_templates`, `comms.sms_delivery_log` (enhanced), `comms.sms_usage_meter` |
| 10 | **Required APIs** | `POST /api/v1/integrations/sms/send`, `GET /api/v1/integrations/sms/delivery-status/{id}`, `PUT /api/v1/tenant/integrations/sms/config`, `GET /api/v1/tenant/sms/usage` |
| 11 | **Required UI Screens** | SMS Gateway Configuration, Template Manager (DLT), Delivery Report, SMS Usage Dashboard |
| 12 | **RBAC Impact** | Permission: `integrations:sms_manage` (admin). System sends automated SMS; staff trigger via workflows. |
| 13 | **Multi-Tenant Considerations** | SMS sender ID per tenant; DLT templates registered per tenant; usage metered per tenant for billing. |
| 14 | **Dependencies** | Notification Module (MVP basic), Usage-Based Billing |
| 15 | **Revenue Impact** | Medium — per-SMS margin revenue; +₹500–₹2,000/month + per-SMS fees |
| 16 | **Recommended Subscription Plan** | All plans (metered) |
| 17 | **Future Enhancements** | Multi-gateway failover, regional gateway selection, SMS campaign management, two-way SMS |

---

### 7.3 Email Integration

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | Email Service Integration |
| 2 | **Category** | Communication Integration |
| 3 | **Business Problem Solved** | Transactional emails (reports, bills, receipts) need reliable delivery with tenant branding and delivery tracking. |
| 4 | **Business Value** | Professional branded email communication; delivery tracking; report/bill delivery automation; reduces manual email workload. |
| 5 | **Target Users** | All Staff (automated), Hospital Admin |
| 6 | **Development Priority** | P2 |
| 7 | **Complexity Level** | Low |
| 8 | **Estimated Development Effort** | 3–4 developer-weeks |
| 9 | **Required Database Tables** | `comms.email_configs`, `comms.email_templates`, `comms.email_delivery_log` (enhanced) |
| 10 | **Required APIs** | `POST /api/v1/integrations/email/send`, `GET /api/v1/integrations/email/delivery-status/{id}`, `PUT /api/v1/tenant/integrations/email/config`, `GET/PUT /api/v1/tenant/email-templates` |
| 11 | **Required UI Screens** | Email Configuration, Template Editor (HTML), Delivery Log, Test Email Sender |
| 12 | **RBAC Impact** | Permission: `integrations:email_manage` (admin). Automated emails via system workflows. |
| 13 | **Multi-Tenant Considerations** | Custom sender domain per tenant (Enterprise); templates branded per tenant; delivery logs tenant-scoped. |
| 14 | **Dependencies** | Notification Module, White Label Branding |
| 15 | **Revenue Impact** | Low — included in platform; custom domain email as Enterprise perk |
| 16 | **Recommended Subscription Plan** | All plans (basic) / Enterprise (custom domain) |
| 17 | **Future Enhancements** | Email campaign module, open/click tracking, automated drip sequences, HIPAA-compliant email archive |

---

### 7.4 Payment Gateway Integration

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | Payment Gateway Integration |
| 2 | **Category** | Financial Integration |
| 3 | **Business Problem Solved** | Hospitals need online payment collection for bills, appointments, and patient portal; cash-only limits revenue collection efficiency. |
| 4 | **Business Value** | Enables online bill payment; reduces outstanding receivables; supports UPI, cards, net banking; improves patient convenience. |
| 5 | **Target Users** | Patients, Billing Staff, Hospital Admin |
| 6 | **Development Priority** | P1 |
| 7 | **Complexity Level** | Medium |
| 8 | **Estimated Development Effort** | 6–8 developer-weeks |
| 9 | **Required Database Tables** | `billing.payment_gateways`, `billing.online_payment_transactions`, `billing.payment_webhooks`, `billing.refund_records` |
| 10 | **Required APIs** | `POST /api/v1/payments/online/initiate`, `POST /api/v1/payments/online/webhook`, `GET /api/v1/payments/online/{id}/status`, `POST /api/v1/payments/online/{id}/refund`, `PUT /api/v1/tenant/integrations/payment/config` |
| 11 | **Required UI Screens** | Payment Gateway Configuration, Online Payment Checkout, Payment Status Tracker, Refund Management, Online Payment Report |
| 12 | **RBAC Impact** | Patients pay via portal (no staff RBAC). Permissions: `payments:online_manage` (admin), `payments:refund` (accountant). |
| 13 | **Multi-Tenant Considerations** | Payment gateway credentials per tenant; settlements to tenant bank account; transaction records tenant-scoped; PCI compliance via gateway tokenization. |
| 14 | **Dependencies** | Billing Module, Patient Portal, Online Appointment Booking |
| 15 | **Revenue Impact** | High — transaction fee revenue; +₹2,000–₹5,000/month + per-transaction margin |
| 16 | **Recommended Subscription Plan** | Professional / Enterprise |
| 17 | **Future Enhancements** | Recurring payments for health packages, split payments, EMI options, multi-currency support |

---

### 7.5 Insurance Provider Integration

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | Insurance Provider / TPA API Integration |
| 2 | **Category** | Financial Integration |
| 3 | **Business Problem Solved** | Manual insurance claim submission and status tracking is slow; TPAs offer APIs for electronic claims that hospitals cannot utilize. |
| 4 | **Business Value** | Electronic claim submission reduces processing time by 70%; real-time claim status; faster settlements; reduced rejection rates. |
| 5 | **Target Users** | Insurance Desk Staff, Accountants, Hospital Admin |
| 6 | **Development Priority** | P2 |
| 7 | **Complexity Level** | High |
| 8 | **Estimated Development Effort** | 12–14 developer-weeks |
| 9 | **Required Database Tables** | `billing.insurance_api_configs`, `billing.insurance_api_transactions`, `billing.e_claims`, `billing.e_claim_responses`, `billing.insurance_eligibility_checks` |
| 10 | **Required APIs** | `POST /api/v1/integrations/insurance/eligibility-check`, `POST /api/v1/integrations/insurance/e-claim`, `GET /api/v1/integrations/insurance/claim-status/{id}`, `POST /api/v1/integrations/insurance/pre-auth`, `PUT /api/v1/tenant/integrations/insurance/config` |
| 11 | **Required UI Screens** | Insurance API Configuration, Eligibility Check Form, E-Claim Submission, Claim Status Tracker, Settlement Reconciliation |
| 12 | **RBAC Impact** | Permission: `integrations:insurance_api` — Insurance Desk, Accountant. |
| 13 | **Multi-Tenant Considerations** | TPA credentials per tenant; e-claims tagged with `tenant_id`; provider catalog system-seeded with tenant enrollment. |
| 14 | **Dependencies** | Insurance Claims Management (Phase 4), Billing Module |
| 15 | **Revenue Impact** | High — major value for insurance-heavy hospitals; +₹5,000–₹10,000/month |
| 16 | **Recommended Subscription Plan** | Enterprise |
| 17 | **Future Enhancements** | Cashless workflow automation, multi-TPA support, denial management, real-time eligibility at registration |

---

### 7.6 PACS Integration

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | PACS (Picture Archiving and Communication System) Integration |
| 2 | **Category** | Clinical Integration |
| 3 | **Business Problem Solved** | Radiology images (X-ray, CT, MRI) are stored in separate PACS systems disconnected from the patient record in HMS. |
| 4 | **Business Value** | Unified patient record with imaging access; eliminates CD/film distribution; enables radiologist workflow within HMS; supports tele-radiology. |
| 5 | **Target Users** | Radiologists, Doctors, Lab Technicians, Patients (via portal) |
| 6 | **Development Priority** | P2 |
| 7 | **Complexity Level** | High |
| 8 | **Estimated Development Effort** | 10–12 developer-weeks |
| 9 | **Required Database Tables** | `clinical.pacs_studies`, `clinical.pacs_series`, `clinical.pacs_images` (metadata only), `clinical.pacs_viewer_configs`, `clinical.radiology_reports` |
| 10 | **Required APIs** | `GET /api/v1/pacs/studies` (by patient), `GET /api/v1/pacs/studies/{id}`, `GET /api/v1/pacs/studies/{id}/viewer-url`, `POST /api/v1/pacs/webhook` (study completion), `POST /api/v1/pacs/reports` |
| 11 | **Required UI Screens** | Radiology Study List (per patient), DICOM Viewer (embedded), Radiology Report Editor, PACS Configuration (admin), Study-Report Linking |
| 12 | **RBAC Impact** | Permissions: `pacs:view` (doctor, radiologist), `pacs:report` (radiologist), `pacs:manage` (admin). Patients view via portal. |
| 13 | **Multi-Tenant Considerations** | PACS server per tenant or shared with tenant routing; DICOM metadata tagged with `tenant_id`; images stored in tenant-scoped storage. |
| 14 | **Dependencies** | Laboratory/Radiology Module, Patient Management, Patient Portal |
| 15 | **Revenue Impact** | Medium — required for imaging centers; +₹3,000–₹6,000/month |
| 16 | **Recommended Subscription Plan** | Enterprise |
| 17 | **Future Enhancements** | AI radiology analysis, teleradiology workflow, DICOM routing, radiation dose tracking |

---

### 7.7 HL7 Integration

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | HL7 v2 Integration |
| 2 | **Category** | Healthcare Interoperability |
| 3 | **Business Problem Solved** | Hospitals need to exchange clinical data (ADT, ORU, ORM) with external systems (lab analyzers, radiology, other HMS) using HL7 v2 standard. |
| 4 | **Business Value** | Enables lab analyzer auto-result import; ADT messaging for referrals; reduces manual data entry; healthcare interoperability compliance. |
| 5 | **Target Users** | Lab Technicians, Hospital IT, Hospital Admin |
| 6 | **Development Priority** | P2 |
| 7 | **Complexity Level** | High |
| 8 | **Estimated Development Effort** | 10–12 developer-weeks |
| 9 | **Required Database Tables** | `integrations.hl7_endpoints`, `integrations.hl7_message_log`, `integrations.hl7_message_queue`, `integrations.hl7_mapping_configs` |
| 10 | **Required APIs** | `POST /api/v1/integrations/hl7/receive` (MLLP), `GET /api/v1/integrations/hl7/messages`, `POST /api/v1/integrations/hl7/send`, `GET/PUT /api/v1/integrations/hl7/config`, `GET /api/v1/integrations/hl7/message-log` |
| 11 | **Required UI Screens** | HL7 Endpoint Configuration, Message Mapping Editor, Message Log Viewer, Queue Monitor, Connection Test Tool |
| 12 | **RBAC Impact** | Permission: `integrations:hl7_manage` — Hospital IT, Admin. |
| 13 | **Multi-Tenant Considerations** | HL7 endpoints per tenant; message routing by tenant identifier in MSH segment; message logs tenant-scoped. |
| 14 | **Dependencies** | Laboratory Module, Patient Management, IPD (ADT messages) |
| 15 | **Revenue Impact** | Medium — enterprise requirement; +₹3,000–₹8,000/month |
| 16 | **Recommended Subscription Plan** | Enterprise |
| 17 | **Future Enhancements** | HL7 FHIR gateway, message validation engine, integration marketplace, pre-built device connectors |

---

### 7.8 FHIR Integration

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | FHIR (Fast Healthcare Interoperability Resources) API |
| 2 | **Category** | Healthcare Interoperability |
| 3 | **Business Problem Solved** | Modern healthcare ecosystem requires FHIR-compliant APIs for patient data exchange, government health ID integration, and third-party app connectivity. |
| 4 | **Business Value** | Future-proof interoperability; enables ABHA (India) integration; supports health app ecosystem; regulatory compliance for data portability. |
| 5 | **Target Users** | Hospital IT, Third-Party Developers, Patients, Platform Admin |
| 6 | **Development Priority** | P2 |
| 7 | **Complexity Level** | High |
| 8 | **Estimated Development Effort** | 12–14 developer-weeks |
| 9 | **Required Database Tables** | `integrations.fhir_resources` (mapping), `integrations.fhir_api_clients`, `integrations.fhir_access_tokens`, `integrations.fhir_audit_log` |
| 10 | **Required APIs** | `GET /api/v1/fhir/Patient`, `GET /api/v1/fhir/Observation`, `GET /api/v1/fhir/MedicationRequest`, `GET /api/v1/fhir/Encounter`, `GET /api/v1/fhir/DiagnosticReport`, `POST /api/v1/fhir/Bundle`, `GET /api/v1/fhir/metadata` |
| 11 | **Required UI Screens** | FHIR API Documentation (auto-generated), API Client Management, Access Token Manager, FHIR Resource Browser (debug), Consent Management for FHIR access |
| 12 | **RBAC Impact** | FHIR access via OAuth2 scopes. Permissions: `fhir:read`, `fhir:write`. Patient consent required for third-party access. |
| 13 | **Multi-Tenant Considerations** | FHIR base URL per tenant subdomain; resources filtered by `tenant_id`; SMART on FHIR launch context includes tenant. |
| 14 | **Dependencies** | All clinical modules, Digital Health Records, API v1, Patient Consent Management |
| 15 | **Revenue Impact** | Medium-High — government mandate alignment; +₹5,000–₹10,000/month |
| 16 | **Recommended Subscription Plan** | Enterprise |
| 17 | **Future Enhancements** | SMART on FHIR app gallery, ABHA integration, bulk FHIR export, international FHIR profiles (US Core, IPS) |

---

### 7.9 Laboratory Device Integration

| # | Field | Detail |
|---|-------|--------|
| 1 | **Feature Name** | Laboratory Device / Analyzer Integration |
| 2 | **Category** | Clinical Integration |
| 3 | **Business Problem Solved** | Lab technicians manually transcribe results from analyzers into HMS, causing errors, delays, and increased turnaround time. |
| 4 | **Business Value** | Eliminates manual result entry; reduces TAT by 40%; eliminates transcription errors; auto-validates result ranges. |
| 5 | **Target Users** | Lab Technicians, Lab Directors, Hospital IT |
| 6 | **Development Priority** | P1 |
| 7 | **Complexity Level** | High |
| 8 | **Estimated Development Effort** | 10–12 developer-weeks |
| 9 | **Required Database Tables** | `integrations.lab_devices`, `integrations.lab_device_mappings`, `integrations.lab_device_results_queue`, `integrations.lab_device_heartbeat` |
| 10 | **Required APIs** | `POST /api/v1/integrations/lab-devices/results` (device push), `GET /api/v1/integrations/lab-devices`, `PUT /api/v1/integrations/lab-devices/{id}/config`, `GET /api/v1/integrations/lab-devices/{id}/status`, `POST /api/v1/integrations/lab-devices/{id}/map-test` |
| 11 | **Required UI Screens** | Device Registration & Configuration, Test Code Mapping, Auto-Result Queue (pending review), Device Status Monitor, Result Validation Panel |
| 12 | **RBAC Impact** | Permission: `integrations:lab_device_manage` (admin/IT). Lab tech: `lab:device_results_review`. |
| 13 | **Multi-Tenant Considerations** | Devices registered per tenant; result queue tenant-scoped; device communication via tenant-specific endpoints or middleware. |
| 14 | **Dependencies** | Laboratory Module, HL7 Integration (recommended) |
| 15 | **Revenue Impact** | Medium — high value for diagnostic centers; +₹3,000–₹6,000/month |
| 16 | **Recommended Subscription Plan** | Professional (diagnostic) / Enterprise |
| 17 | **Future Enhancements** | Pre-built connectors for popular analyzers, bidirectional order sending, QC data import, auto-approval for normal results |

---

## 8. Feature Priority Matrix

Cross-phase prioritization based on business impact, customer demand, and implementation readiness.

| Priority | Feature | Phase | Complexity | Revenue Impact | Retention Impact |
|----------|---------|-------|------------|----------------|------------------|
| **P1** | Insurance Claims Management | 4 | High | Very High | High |
| **P1** | Operation Theater Management | 4 | High | High | High |
| **P1** | ICU Management | 4 | High | High | High |
| **P1** | Emergency Department | 4 | Medium | Medium-High | High |
| **P1** | Multi-Branch Management | 5 | High | High | Very High |
| **P1** | Feature Flags | 5 | Medium | Indirect | High |
| **P1** | Subscription Analytics | 5 | Medium | Indirect | High |
| **P1** | Patient Portal | 6 | High | Medium | Very High |
| **P1** | Mobile Application | 6 | High | High | Very High |
| **P1** | Online Appointment Booking | 6 | Medium | Medium-High | High |
| **P1** | Digital Health Records | 6 | High | Medium | High |
| **P1** | AI Symptom Analyzer | 7 | Medium | Medium | Medium |
| **P1** | AI Prescription Assistant | 7 | Medium | High | High |
| **P1** | AI Clinical Notes Generator | 7 | Medium | High | High |
| **P1** | AI Revenue Analytics | 7 | Medium | Very High | High |
| **P1** | Executive Analytics Dashboard | 8 | High | High | Very High |
| **P1** | WhatsApp Integration | 9 | Medium | Medium | High |
| **P1** | SMS Integration | 9 | Low | Medium | Medium |
| **P1** | Payment Gateway Integration | 9 | Medium | High | High |
| **P1** | Laboratory Device Integration | 9 | High | Medium | High |
| **P2** | Blood Bank Management | 4 | High | Medium | Medium |
| **P2** | Ambulance Management | 4 | Medium | Medium | Medium |
| **P2** | Vaccination Management | 4 | Medium | Medium | Medium |
| **P2** | White Label Branding | 5 | Medium | Medium | High |
| **P2** | Custom Domain Support | 5 | Medium | Medium | Medium |
| **P2** | Advanced Tenant Settings | 5 | Medium | Low-Medium | Medium |
| **P2** | Usage-Based Billing | 5 | High | High | Medium |
| **P2** | Doctor Portal | 6 | Medium | Medium | Medium |
| **P2** | Telemedicine | 6 | High | High | High |
| **P2** | Patient Feedback System | 6 | Low | Low-Medium | Medium |
| **P2** | AI Discharge Summary | 7 | Medium | Medium | Medium |
| **P2** | AI Medical Report Summarizer | 7 | Medium | Medium | Medium |
| **P2** | AI Voice to Clinical Notes | 7 | High | High | High |
| **P2** | AI Inventory Forecasting | 7 | Medium | Medium | Medium |
| **P2** | AI Follow-Up Assistant | 7 | Medium | Medium | Medium |
| **P2** | Corporate Health Packages | 8 | Medium | Medium | Medium |
| **P2** | HR & Payroll | 8 | High | Medium | Medium |
| **P2** | Compliance Management | 8 | Medium | Medium | High |
| **P2** | Audit Management | 8 | Medium | Medium | High |
| **P2** | Business Intelligence Reports | 8 | High | Medium-High | High |
| **P2** | Email Integration | 9 | Low | Low | Medium |
| **P2** | Insurance Provider Integration | 9 | High | High | High |
| **P2** | PACS Integration | 9 | High | Medium | Medium |
| **P2** | HL7 Integration | 9 | High | Medium | Medium |
| **P2** | FHIR Integration | 9 | High | Medium-High | High |
| **P3** | AI Chat Assistant | 7 | Medium | Low-Medium | Medium |
| **P3** | Data Warehouse Integration | 8 | High | Medium | Medium |

---

## 9. Revenue Opportunity Matrix

Estimated revenue impact per feature category for the SaaS platform operator.

| Revenue Tier | Features | Est. ARPU Impact | Pricing Model |
|-------------|----------|------------------|---------------|
| **Tier 1 — High ARPU (₹5,000+/month)** | Insurance Claims, OT Management, ICU, Multi-Branch, Executive Analytics, AI Revenue Analytics, Insurance API, FHIR, Data Warehouse | +₹5,000–₹15,000/tenant/month | Enterprise plan upgrade or premium add-on |
| **Tier 2 — Medium ARPU (₹2,000–₹5,000/month)** | ED, Patient Portal, Mobile App, Telemedicine, AI Prescription, AI Notes, Payment Gateway, PACS, HL7, Lab Devices, HR & Payroll, BI Reports | +₹2,000–₹5,000/tenant/month | Professional add-on or Enterprise included |
| **Tier 3 — Usage Revenue** | SMS, WhatsApp, AI features (metered), Online Payments (transaction fee) | Variable; ₹500–₹3,000/tenant/month + usage | Per-unit metering on all plans |
| **Tier 4 — Retention Revenue** | Feature Flags, Branding, Custom Domain, Feedback, Compliance, Audit, Digital Health Records | Indirect; reduces churn 2–5% | Included in plan tiers; reduces CAC payback |

### 9.1 Projected Revenue Impact by Phase

| Phase | Timeline | Cumulative ARPU Increase | Target Tenant Count | Incremental ARR |
|-------|----------|-------------------------|--------------------|--------------------|
| Phase 4 | Q1–Q2 2027 | +₹8,000–₹15,000/month | 50 → 75 | ₹72L – ₹1.35Cr |
| Phase 5 | Q2–Q3 2027 | +₹5,000–₹10,000/month | 75 → 100 | ₹45L – ₹90L |
| Phase 6 | Q3 2027 – Q1 2028 | +₹5,000–₹12,000/month | 100 → 150 | ₹60L – ₹1.44Cr |
| Phase 7 | Q2–Q4 2027 | +₹3,000–₹8,000/month | 150 → 200 | ₹54L – ₹1.44Cr |
| Phase 8 | Q4 2027 – Q2 2028 | +₹5,000–₹12,000/month | 200 → 250 | ₹1.2Cr – ₹2.88Cr |
| Phase 9 | Q1–Q4 2028 | +₹3,000–₹8,000/month | 250 → 350 | ₹90L – ₹2.4Cr |

---

## 10. Development Order Recommendation

Recommended build sequence optimized for dependencies, revenue impact, and team capacity. Phases may overlap; within each phase, build in listed order.

### 10.1 Phase 4 Build Order

```
1. Emergency Department        → fastest value; extends OPD
2. Insurance Claims Management   → highest revenue impact
3. Operation Theater Management  → Enterprise upsell
4. ICU Management                → depends on IPD depth
5. Vaccination Management        → lower complexity win
6. Blood Bank Management         → niche; build on lab
7. Ambulance Management          → depends on ED
```

### 10.2 Phase 5 Build Order

```
1. Feature Flags                 → enables safe rollout of all future features
2. Subscription Analytics        → platform operator visibility
3. Multi-Branch Management       → unlocks chain hospitals
4. Advanced Tenant Settings      → reduces support load
5. Usage-Based Billing           → monetization infrastructure
6. White Label Branding          → Enterprise differentiator
7. Custom Domain Support         → depends on branding
```

### 10.3 Phase 6 Build Order

```
1. Online Appointment Booking    → public-facing; drives acquisition
2. Patient Portal                → foundation for patient experience
3. Digital Health Records        → unified record view
4. Patient Feedback System       → quick win; low complexity
5. Mobile Application (Staff)    → React Native; staff-first
6. Doctor Portal                 → extends mobile/web for doctors
7. Telemedicine                  → depends on portal + booking
8. Mobile Application (Patient)  → extends patient portal
```

### 10.4 Phase 7 Build Order

```
1. AI Clinical Notes Generator   → highest doctor demand
2. AI Prescription Assistant     → safety-critical value
3. AI Symptom Analyzer           → extends consultation AI
4. AI Revenue Analytics          → admin-facing; clear ROI
5. AI Medical Report Summarizer  → lab workflow improvement
6. AI Discharge Summary          → IPD workflow
7. AI Inventory Forecasting      → pharmacy operations
8. AI Follow-Up Assistant        → patient engagement
9. AI Voice to Clinical Notes    → complex; builds on notes generator
10. AI Chat Assistant            → platform-wide; lower priority
```

### 10.5 Phase 8 Build Order

```
1. Executive Analytics Dashboard → leadership visibility
2. Business Intelligence Reports → self-service reporting
3. Audit Management              → compliance foundation
4. Compliance Management         → accreditation support
5. Corporate Health Packages     → B2B revenue
6. HR & Payroll                  → large scope; independent
7. Data Warehouse Integration    → enterprise IT requirement
```

### 10.6 Phase 9 Build Order

```
1. SMS Integration (enhanced)    → low complexity; immediate value
2. Payment Gateway Integration   → revenue enabler
3. WhatsApp Integration          → patient engagement
4. Laboratory Device Integration → diagnostic center value
5. Email Integration (enhanced)  → completes comms stack
6. HL7 Integration               → foundation for device/PACS
7. Insurance Provider Integration → extends Phase 4 claims
8. PACS Integration              → depends on HL7
9. FHIR Integration              → modern interoperability capstone
```

---

## 11. MVP vs Future Features Comparison

| Dimension | MVP (Phases 1–3) | Advanced Features (Phases 4–9) |
|-----------|------------------|----------------------------------|
| **Scope** | Core HMS: OPD, Patient, Billing, IPD, Lab, Pharmacy, Admin, Subscription | Specialized departments, patient portals, AI, enterprise analytics, integrations |
| **Target User** | Hospital staff (internal) | Staff + patients + external doctors + corporate clients + platform operator |
| **Tenant Count Target** | 10 → 50 | 50 → 350+ |
| **ARPU** | ₹5,000–₹15,000/month | ₹15,000–₹50,000/month |
| **Subscription Plans** | Starter, Professional, Enterprise (basic) | Plan differentiation via add-ons, usage billing, module toggles |
| **Clinical Modules** | 5 (OPD, IPD, Lab, Pharmacy, Billing) | +7 premium (OT, ICU, ED, Blood Bank, Ambulance, Insurance, Vaccination) |
| **Patient-Facing** | None (staff-only web app) | Portal, mobile app, online booking, telemedicine, feedback |
| **AI Features** | None | 10 AI-assisted features |
| **Integrations** | Basic SMS/email notifications | 9 external integrations (WhatsApp, payment, HL7, FHIR, PACS, etc.) |
| **Analytics** | Operational reports, basic dashboard | Executive dashboard, BI reports, AI analytics, data warehouse |
| **Customization** | Subdomain, basic settings | White-label, custom domain, feature flags, advanced settings |
| **Compliance** | Audit logs, RBAC, encryption | Compliance management, advanced audit, accreditation support |
| **Team Size** | 7–13 | 15–25 |
| **Tech Investment** | ₹50K–₹1.2L/month infra | ₹1.5L–₹3L/month infra (+ AI costs) |

### 11.1 Feature Count Summary

| Category | MVP | Advanced | Total |
|----------|-----|----------|-------|
| Clinical Modules | 5 | 7 | 12 |
| SaaS Platform | 4 | 7 | 11 |
| Patient Experience | 0 | 7 | 7 |
| AI Features | 0 | 10 | 10 |
| Enterprise | 2 | 7 | 9 |
| Integrations | 2 | 9 | 11 |
| **Total Features** | **13** | **47** | **60** |

---

## 12. Estimated Timeline After MVP

Assumes MVP completion in Q4 2026 with a team scaling from 10 to 25 engineers.

```
2027                                    2028
Q1          Q2          Q3          Q4          Q1          Q2          Q3          Q4
│           │           │           │           │           │           │           │
├───────────┤           │           │           │           │           │           │
│ Phase 4   │           │           │           │           │           │           │
│ Premium   │           │           │           │           │           │           │
│ Hospital  │           │           │           │           │           │           │
├───────────┼───────────┤           │           │           │           │           │
│           │ Phase 5   │           │           │           │           │           │
│           │ SaaS      │           │           │           │           │           │
│           │ Growth    │           │           │           │           │           │
├───────────┼───────────┼───────────┤           │           │           │           │
│           │ Phase 7   │ Phase 6   │           │           │           │           │
│           │ AI (start)│ Patient   │           │           │           │           │
│           │           │ Experience│           │           │           │           │
│           ├───────────┼───────────┼───────────┤           │           │           │
│           │           │ Phase 7   │ Phase 8   │           │           │           │
│           │           │ AI (cont.)│ Enterprise│           │           │           │
│           │           │           ├───────────┼───────────┼───────────┤           │
│           │           │           │           │ Phase 9   │ Phase 9   │ Phase 9   │
│           │           │           │           │ Integr.   │ Integr.   │ Integr.   │
│           │           │           │           │ (start)   │ (cont.)   │ (complete)│
```

### 12.1 Phase Milestones

| Milestone | Target Date | Deliverables | Success Metric |
|-----------|-------------|--------------|----------------|
| M7: Premium Clinical | Jun 2027 | OT, ICU, ED, Insurance Claims live | 30% Enterprise adoption |
| M8: SaaS Growth | Sep 2027 | Multi-branch, feature flags, usage billing | 10 chain hospital tenants |
| M9: Patient Experience | Dec 2027 | Patient portal, online booking, mobile app (staff) | 20% patient portal adoption |
| M10: AI Launch | Sep 2027 | 3+ AI features in production | 25% AI feature adoption |
| M11: Enterprise Suite | Mar 2028 | Executive analytics, BI reports, compliance | 5 Enterprise upsells |
| M12: Integration Hub | Dec 2028 | Payment, WhatsApp, HL7, lab devices live | 3+ integrations per Enterprise tenant |
| M13: Full Platform | Dec 2028 | All 47 advanced features GA | 350 active tenants, ₹50L+ MRR |

### 12.2 Team Scaling Plan

| Period | Engineers | Focus |
|--------|-----------|-------|
| Q1 2027 | 10–12 | Phase 4 (Premium Clinical) |
| Q2 2027 | 12–15 | Phase 4 completion + Phase 5 + Phase 7 (AI start) |
| Q3 2027 | 15–18 | Phase 6 (Patient Experience) + Phase 7 (AI) |
| Q4 2027 | 18–20 | Phase 8 (Enterprise) + Phase 7 completion |
| Q1–Q4 2028 | 20–25 | Phase 9 (Integrations) + hardening |

---

## 13. Recommended Subscription Strategy

### 13.1 Evolved Plan Structure (Post-MVP)

| Plan | Monthly Price | Target Segment | Core Modules | Advanced Add-Ons |
|------|--------------|----------------|--------------|------------------|
| **Starter** | ₹4,999 | Clinics | OPD, Patient, Billing | Online Booking, SMS, Patient Portal |
| **Professional** | ₹14,999 | Small Hospitals | + IPD, Lab, Pharmacy, Reports | ED, Vaccination, AI (basic), Mobile (staff), WhatsApp |
| **Enterprise** | ₹29,999+ | Medium Hospitals / Chains | All MVP + Premium Clinical | All AI, Patient App, Telemedicine, Integrations, Analytics |
| **Custom** | Negotiated | Large Chains / Groups | Everything | White-label, custom domain, data warehouse, dedicated support |

### 13.2 Add-On Pricing Model

| Add-On Category | Pricing | Available On |
|----------------|---------|--------------|
| Premium Clinical Module (per module) | ₹2,000–₹5,000/month | Professional+ |
| AI Features Pack | ₹3,000–₹8,000/month | Professional+ |
| Patient Portal + Online Booking | ₹2,000/month | Starter+ |
| Mobile App (Patient) | ₹3,000/month | Professional+ |
| Telemedicine | ₹3,000/month + per-session | Professional+ |
| Integration (per integration) | ₹2,000–₹5,000/month | Enterprise |
| Additional Branch | ₹5,000–₹10,000/month | Enterprise |
| White Label + Custom Domain | ₹5,000/month | Enterprise |
| Usage: SMS | ₹0.15–₹0.25/SMS | All plans |
| Usage: WhatsApp | ₹0.50–₹1.00/message | Professional+ |
| Usage: AI Invocations | ₹5–₹15/invocation | Professional+ |
| Usage: Online Payment | 1.5–2.0% transaction fee | All plans |

### 13.3 Expansion Revenue Strategy

```
Land (Starter/Professional)
  │
  ├── Module Upsell → Premium Clinical add-ons
  ├── Seat Expansion → Additional users beyond plan limit
  ├── AI Upsell → AI features pack
  ├── Patient Channel → Portal + Mobile + Booking
  ├── Integration Upsell → Payment, WhatsApp, HL7
  └── Plan Upgrade → Enterprise (all-inclusive)
```

### 13.4 Key Metrics to Track

| Metric | Target (Post-Advanced Features) |
|--------|--------------------------------|
| Net Revenue Retention (NRR) | > 120% |
| Expansion Revenue % of MRR | > 25% |
| Average Add-Ons per Tenant | > 2 |
| Enterprise Plan % of Tenants | > 20% |
| AI Feature Attach Rate | > 30% |
| Patient Portal Adoption | > 40% of tenants |
| Integration Attach Rate (Enterprise) | > 3 integrations |

---

## 14. Document Governance

| Review | Frequency | Participants | Output |
|--------|-----------|-------------|--------|
| Feature Prioritization | Quarterly | Product, Engineering, Sales, CS | Reprioritized backlog |
| Phase Gate Review | End of each phase | Leadership, Product, Engineering | Go/No-Go for next phase |
| Revenue Impact Review | Monthly | Product, Finance, Sales | ARPU tracking, pricing adjustments |
| Customer Feature Requests | Ongoing | Product, CS | Evaluated against this roadmap |

### 14.1 Change Management

- Features may be reprioritized based on customer demand and competitive landscape
- New features discovered during development are added to this document, not to MVP scope
- Scope additions require identification of trade-offs against existing planned features
- Customer-driven expedites require Executive approval and timeline adjustment

---

## 15. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | June 2026 | Product Architecture Team | Initial advanced features roadmap (Phases 4–9) |

---

*This document is the authoritative reference for post-MVP feature planning. MVP scope is defined in ROADMAP.md (Phases 1–3), PRD.md, and FUNCTIONAL_REQUIREMENTS.md. No feature in this document shall be implemented during MVP development without explicit Executive approval and MVP scope amendment.*
