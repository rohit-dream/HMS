# Product Roadmap

## Multi-Tenant Hospital Management SaaS Platform

| Field | Value |
|-------|-------|
| **Document Version** | 1.0 |
| **Status** | Draft |
| **Last Updated** | June 2026 |
| **Planning Horizon** | 18 months (Q3 2026 – Q4 2027) |
| **Related Documents** | PRD.md, SPRINT_PLAN.md, BUSINESS_REQUIREMENTS.md |

---

## 1. Roadmap Overview

This roadmap defines the phased delivery plan for the Multi-Tenant Hospital Management SaaS Platform. Each phase builds upon the previous, delivering incremental value while maintaining a production-quality, secure, and scalable system.

### 1.1 Strategic Themes

| Theme | Description |
|-------|-------------|
| **Foundation** | Multi-tenant platform, auth, subscription, core workflows |
| **Clinical Depth** | IPD, laboratory, pharmacy modules |
| **Business Intelligence** | Analytics, reporting, revenue optimization |
| **Intelligence** | AI-assisted features for clinical and operational efficiency |
| **Ecosystem** | APIs, integrations, mobile, international expansion |

### 1.2 Roadmap Timeline

```
2026                                    2027
Q3          Q4          Q1          Q2          Q3          Q4
│           │           │           │           │           │
├───────────┤           │           │           │           │
│ Phase 1   │           │           │           │           │
│ MVP       │           │           │           │           │
├───────────┼───────────┤           │           │           │
│           │ Phase 2   │           │           │           │
│           │ Clinical  │           │           │           │
│           ├───────────┼───────────┤           │           │
│           │           │ Phase 3   │           │           │
│           │           │ Analytics │           │           │
│           │           ├───────────┼───────────┤           │
│           │           │           │ Phase 4   │           │
│           │           │           │ AI        │           │
│           │           │           ├───────────┼───────────┤
│           │           │           │           │ Phase 5   │
│           │           │           │           │ Ecosystem │
```

---

## 2. Vision & Goals

### 2.1 Long-Term Vision (2027)

Become the leading hospital management SaaS platform for SMB healthcare providers in emerging markets, serving 5,000+ tenants with a comprehensive, AI-enhanced, and integration-rich ecosystem.

### 2.2 Roadmap Goals

| Goal | Target Date | Metric |
|------|-------------|--------|
| MVP launch with paying customers | Q3 2026 | 10 paying tenants |
| Full clinical suite (OPD + IPD + Lab + Pharmacy) | Q4 2026 | All modules live |
| Product-market fit | Q1 2027 | NPS ≥ 40, churn < 5% |
| 50 active tenants | Q1 2027 | 50 paying tenants |
| AI features in production | Q2 2027 | 2+ AI features live |
| ₹50L ARR | Q2 2027 | ₹50,00,000 annual revenue |
| Mobile app launch | Q3 2027 | iOS + Android apps |
| API marketplace | Q4 2027 | 3+ integration partners |

---

## 3. Phase 1: Foundation & MVP

**Timeline:** Q3 2026 (July – September 2026)  
**Theme:** Core platform with OPD, patient management, and billing  
**Target:** 10 beta tenants, production launch

### 3.1 Objectives

- Establish multi-tenant architecture with shared database and `tenant_id` isolation
- Deliver core hospital workflows: patient registration → OPD consultation → billing
- Enable self-service tenant onboarding with subscription billing
- Launch production environment with 99.9% uptime target

### 3.2 Deliverables

| Module | Features | Priority |
|--------|----------|----------|
| **Platform** | Tenant provisioning, organization profile, subdomain | P0 |
| **Multi-Tenancy** | `tenant_id` isolation, middleware enforcement, isolation tests | P0 |
| **Authentication** | Email/password login, JWT, password reset, session management | P0 |
| **RBAC** | Predefined roles (Admin, Doctor, Receptionist, Billing), permission enforcement | P0 |
| **Subscription** | Plans (Starter/Pro/Enterprise), 14-day trial, automated billing, plan limits | P0 |
| **Patient Management** | Registration, MRN, search, profile, allergies, visit history | P0 |
| **OPD** | Appointments, queue management, consultation, vitals, e-prescription | P0 |
| **Billing** | Service master, OPD billing, payments, receipts, daily collection report | P0 |
| **Administration** | Staff management, departments, doctor profiles, system config, audit logs | P0 |
| **Frontend** | React + TypeScript + TailwindCSS responsive web app | P0 |
| **Backend** | FastAPI + Python REST API with OpenAPI documentation | P0 |
| **Database** | SQL schema with migrations, seed data, `tenant_id` on all tables | P0 |
| **Infrastructure** | Cloud deployment, CI/CD, monitoring, backups | P0 |

### 3.3 Sprint Breakdown (Indicative)

| Sprint | Duration | Focus |
|--------|----------|-------|
| Sprint 1 | 2 weeks | Project setup, database schema, multi-tenant middleware |
| Sprint 2 | 2 weeks | Authentication, RBAC, tenant management |
| Sprint 3 | 2 weeks | Patient management module |
| Sprint 4 | 2 weeks | OPD: appointments, queue |
| Sprint 5 | 2 weeks | OPD: consultation, e-prescription |
| Sprint 6 | 2 weeks | Billing module |
| Sprint 7 | 2 weeks | Subscription management, admin panel |
| Sprint 8 | 2 weeks | Frontend integration, testing, bug fixes |
| Sprint 9 | 2 weeks | Security audit, performance testing, beta launch |

### 3.4 Success Criteria

| Criterion | Target |
|-----------|--------|
| Beta tenants onboarded | 10 |
| Core workflow completion time | < 5 minutes (register → consult → bill) |
| API uptime | 99.9% |
| Zero cross-tenant data leaks | 0 incidents |
| Security audit | Passed |

### 3.5 KPIs (Phase 1 Exit)

| KPI | Target |
|-----|--------|
| Paying tenants | 10 |
| MRR | ₹1,00,000 |
| Trial-to-paid conversion | > 20% |
| Onboarding time | < 4 hours |
| P95 API response | < 500ms |

---

## 4. Phase 2: Clinical Depth

**Timeline:** Q4 2026 (October – December 2026)  
**Theme:** IPD, Laboratory, and Pharmacy modules  
**Target:** 25 active tenants, full clinical suite

### 4.1 Objectives

- Complete the clinical workflow suite for small hospitals
- Enable diagnostic centers with standalone lab module
- Add pharmacy management with inventory tracking
- Improve reporting with operational dashboards

### 4.2 Deliverables

| Module | Features | Priority |
|--------|----------|----------|
| **IPD** | Admission, bed management, nursing notes, discharge summary | P1 |
| **Bed Management** | Ward/bed master, availability dashboard, occupancy tracking | P1 |
| **Laboratory** | Test catalog, sample tracking, result entry, report generation | P1 |
| **Pharmacy** | Drug master, prescription dispensing, inventory management | P1 |
| **IPD Billing** | Daily charges, running bill, discharge billing | P1 |
| **Reporting** | Operational dashboard, OPD/IPD/Lab/Pharmacy reports | P1 |
| **Notifications** | SMS/email appointment reminders, lab result alerts | P1 |
| **Patient Import** | CSV bulk import for data migration | P1 |
| **Multi-Location** | Branch/location support per tenant | P1 |
| **Plan Upgrade** | Self-service plan upgrade with prorated billing | P1 |

### 4.3 Success Criteria

| Criterion | Target |
|-----------|--------|
| Active tenants | 25 |
| IPD module adoption | > 50% of Professional+ tenants |
| Lab module adoption | > 40% of tenants |
| Module-related support tickets | < 3 per tenant/month |

### 4.4 KPIs (Phase 2 Exit)

| KPI | Target |
|-----|--------|
| Active tenants | 25 |
| MRR | ₹2,50,000 |
| Feature adoption (3+ modules) | > 60% |
| NPS | ≥ 30 |
| Churn rate | < 7% |

---

## 5. Phase 3: Business Intelligence & Compliance

**Timeline:** Q1 2027 (January – March 2027)  
**Theme:** Advanced analytics, insurance billing, localization  
**Target:** 50 active tenants, product-market fit

### 5.1 Objectives

- Deliver advanced analytics for hospital administrators
- Support basic insurance/TPA billing workflows
- Add Hindi language support for broader market reach
- Strengthen compliance and data governance features

### 5.2 Deliverables

| Module | Features | Priority |
|--------|----------|----------|
| **Advanced Analytics** | Revenue analytics, doctor performance, department comparison, trends | P1 |
| **Custom Reports** | Report builder with filters, scheduling, email delivery | P2 |
| **Insurance/TPA** | Insurance details on patient, basic claim tracking, TPA billing | P2 |
| **Localization** | Hindi UI translation, multi-language report templates | P2 |
| **Custom Roles** | Tenant-defined roles with granular permissions | P2 |
| **2FA** | TOTP-based two-factor authentication | P2 |
| **Data Export** | Enhanced tenant data export (JSON, CSV, PDF archive) | P1 |
| **Compliance Dashboard** | Consent tracking, access logs, retention policy management | P2 |
| **Customer Success** | In-app onboarding tours, contextual help, knowledge base | P1 |
| **API v1** | Public REST API for Enterprise tenants | P2 |

### 5.3 Success Criteria

| Criterion | Target |
|-----------|--------|
| Active tenants | 50 |
| NPS | ≥ 40 |
| Churn rate | < 5% |
| Hindi language adoption | > 30% of Indian tenants |

### 5.4 KPIs (Phase 3 Exit)

| KPI | Target |
|-----|--------|
| Active tenants | 50 |
| MRR | ₹4,00,000 |
| ARR | ₹48,00,000 |
| NPS | ≥ 40 |
| Churn rate | < 5% |
| LTV:CAC ratio | > 3:1 |

---

## 6. Phase 4: AI & Intelligence

**Timeline:** Q2 2027 (April – June 2027)  
**Theme:** AI-powered features for clinical and operational efficiency  
**Target:** Differentiation through intelligence, upsell revenue

### 6.1 Objectives

- Integrate AI features that provide tangible value to healthcare providers
- Reduce operational inefficiencies through intelligent automation
- Create upsell opportunities with AI-powered premium features
- Establish data foundation for future ML models

### 6.2 Deliverables

| Feature | Description | Priority |
|---------|-------------|----------|
| **Smart Appointment Scheduling** | AI-optimized slot allocation based on historical no-show patterns and doctor availability | P2 |
| **Revenue Leakage Detection** | Identify unbilled services by comparing clinical activities with billing records | P2 |
| **Clinical Decision Support** | Drug interaction warnings, allergy alerts, dosage recommendations | P2 |
| **Predictive Inventory** | Pharmacy stock forecasting based on prescription patterns | P3 |
| **Patient Risk Scoring** | Flag high-risk patients based on vitals trends and chronic conditions | P3 |
| **Automated Coding** | Suggest ICD-10 codes based on clinical notes | P3 |
| **Chatbot Assistant** | In-app AI assistant for staff training and workflow guidance | P3 |
| **Demand Forecasting** | Predict patient volume for staffing and resource planning | P3 |

### 6.3 Success Criteria

| Criterion | Target |
|-----------|--------|
| AI feature adoption | > 30% of tenants using at least one AI feature |
| Revenue leakage recovered | Average ₹10,000/tenant/month identified |
| AI-related upsell revenue | 10% of MRR |

### 6.4 KPIs (Phase 4 Exit)

| KPI | Target |
|-----|--------|
| Active tenants | 100 |
| MRR | ₹8,00,000 |
| AI feature adoption | > 30% |
| Expansion revenue | 15% of MRR |

---

## 7. Phase 5: Ecosystem & Expansion

**Timeline:** Q3–Q4 2027 (July – December 2027)  
**Theme:** Mobile apps, telemedicine, integrations, international expansion  
**Target:** 200+ tenants, platform ecosystem

### 7.1 Objectives

- Launch mobile applications for doctors and patients
- Enable telemedicine capabilities
- Build integration marketplace for third-party services
- Expand to international markets
- Offer white-label solution for hospital chains

### 7.2 Deliverables

| Feature | Description | Priority |
|---------|-------------|----------|
| **Mobile App (Doctor)** | iOS/Android app for appointments, consultations, patient lookup | P2 |
| **Mobile App (Patient)** | iOS/Android app for appointments, reports, bills | P3 |
| **Telemedicine** | Video consultation integration, remote prescribing | P2 |
| **HL7/FHIR API** | Healthcare interoperability standards support | P2 |
| **Integration Marketplace** | Lab equipment, pharmacy suppliers, insurance TPAs | P2 |
| **White-Label** | Custom branding, domain, and deployment for hospital chains | P2 |
| **Multi-Region Deployment** | Data residency options (India, Middle East, Africa) | P2 |
| **Government Integration** | ABHA (India), NPHIES (Saudi) health ID integration | P3 |
| **Partner API SDK** | Developer documentation, SDKs, sandbox environment | P2 |
| **Advanced Subscription** | Usage-based billing, custom enterprise contracts | P2 |

### 7.3 Success Criteria

| Criterion | Target |
|-----------|--------|
| Active tenants | 200 |
| Mobile app downloads | 5,000+ |
| Integration partners | 3+ |
| International tenants | 10+ |

### 7.4 KPIs (Phase 5 Exit)

| KPI | Target |
|-----|--------|
| Active tenants | 200 |
| MRR | ₹15,00,000 |
| ARR | ₹1.8 Cr |
| International revenue | 15% of ARR |
| Mobile DAU | 30% of total DAU |

---

## 8. Future Scope (2028+)

Features and initiatives planned beyond the 18-month roadmap:

| Initiative | Description | Business Value |
|------------|-------------|----------------|
| **IoT Integration** | Bedside monitors, lab analyzers, wearable devices | Real-time vitals, reduced manual entry |
| **Blockchain Health Records** | Patient-controlled health records on blockchain | Data portability, patient empowerment |
| **Population Health Analytics** | Aggregate anonymized insights across tenants (opt-in) | Public health insights, research |
| **AI Diagnostics** | Radiology AI, pathology image analysis | Clinical accuracy, faster diagnosis |
| **Hospital Marketplace** | Patients discover and book appointments across tenant network | Patient acquisition channel for tenants |
| **Embedded Insurance** | Partner with insurers for embedded health plans | New revenue stream |
| **Acquisition Platform** | Acquire smaller health-tech startups for capability expansion | Faster feature development |
| **Offline Mode** | Progressive web app with offline capability for low-connectivity areas | Market expansion to rural areas |
| **Voice Interface** | Voice-driven clinical note entry for doctors | Doctor efficiency, hands-free operation |
| **Carbon Footprint Tracking** | Sustainability reporting for hospital operations | ESG compliance, brand value |

---

## 9. Release Strategy

### 9.1 Release Cadence

| Release Type | Frequency | Description |
|-------------|-----------|-------------|
| **Major Release** | Quarterly | New modules, significant features |
| **Minor Release** | Bi-weekly | Feature enhancements, improvements |
| **Patch Release** | As needed | Bug fixes, security patches |
| **Hotfix** | Emergency | Critical production issues |

### 9.2 Feature Flag Strategy

All new features deployed behind feature flags:

- **Development:** Feature visible in dev environment
- **Staging:** Feature enabled for internal testing
- **Beta:** Feature enabled for selected beta tenants
- **GA:** Feature enabled for all tenants on applicable plan

### 9.3 Beta Program

| Phase | Beta Tenants | Duration | Feedback Channel |
|-------|-------------|----------|-----------------|
| Phase 1 MVP | 5 clinics | 4 weeks pre-launch | Weekly calls, in-app feedback |
| Phase 2 Clinical | 10 hospitals | 4 weeks pre-launch | Bi-weekly calls, survey |
| Phase 3 Analytics | 15 tenants | 3 weeks pre-launch | Survey, feature requests |
| Phase 4 AI | 20 tenants | 6 weeks pre-launch | A/B testing, usage analytics |

---

## 10. Dependencies & Risks

### 10.1 Cross-Phase Dependencies

```
Phase 1 (Foundation)
    │
    ├──▶ Phase 2 (Clinical) ── requires patient, OPD, billing from Phase 1
    │         │
    │         ├──▶ Phase 3 (Analytics) ── requires all clinical data from Phase 2
    │         │         │
    │         │         ├──▶ Phase 4 (AI) ── requires data volume from Phase 3
    │         │         │         │
    │         │         │         └──▶ Phase 5 (Ecosystem) ── requires stable API from Phase 3
```

### 10.2 Key Risks by Phase

| Phase | Risk | Impact | Mitigation |
|-------|------|--------|------------|
| 1 | Multi-tenant isolation failure | Critical | Mandatory isolation tests in CI; pen testing |
| 1 | Delayed MVP launch | High | Strict scope control; MVP-first culture |
| 2 | Low IPD module adoption | Medium | Customer interviews; UX optimization |
| 2 | Lab report compliance issues | Medium | Regulatory review; template customization |
| 3 | Insurance integration complexity | High | Start with basic tracking; phased TPA integration |
| 3 | Hindi translation quality | Medium | Professional translation service; user feedback |
| 4 | AI model accuracy in healthcare | High | Human-in-the-loop; clinician review required |
| 4 | AI infrastructure cost | Medium | Cost monitoring; tiered AI feature access |
| 5 | Mobile app store approval delays | Medium | Early submission; compliance review |
| 5 | International compliance variations | High | Legal review per region; modular compliance |

---

## 11. Investment & Resource Plan

### 11.1 Team Growth

| Phase | Engineering | Product | Design | QA | Total |
|-------|------------|---------|--------|-----|-------|
| Phase 1 | 4 | 1 | 1 | 1 | 7 |
| Phase 2 | 6 | 1 | 1 | 2 | 10 |
| Phase 3 | 8 | 2 | 1 | 2 | 13 |
| Phase 4 | 10 | 2 | 1 | 2 | 15 |
| Phase 5 | 12 | 2 | 2 | 3 | 19 |

### 11.2 Technology Investment

| Category | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 |
|----------|---------|---------|---------|---------|---------|
| Cloud Infrastructure | ₹50K/mo | ₹80K/mo | ₹1.2L/mo | ₹1.5L/mo | ₹2L/mo |
| Third-Party Services | ₹20K/mo | ₹30K/mo | ₹50K/mo | ₹80K/mo | ₹1L/mo |
| AI/ML Infrastructure | — | — | — | ₹50K/mo | ₹80K/mo |
| Security & Compliance | ₹30K/mo | ₹30K/mo | ₹50K/mo | ₹50K/mo | ₹80K/mo |

---

## 12. Milestone Summary

| Milestone | Date | Key Deliverable | Success Metric |
|-----------|------|-----------------|----------------|
| **M1: Architecture Complete** | Aug 2026 | Multi-tenant foundation, auth, database | Isolation tests pass |
| **M2: MVP Launch** | Sep 2026 | OPD + Patient + Billing live | 10 beta tenants |
| **M3: Clinical Suite** | Dec 2026 | IPD + Lab + Pharmacy live | 25 active tenants |
| **M4: Product-Market Fit** | Mar 2027 | Analytics + Insurance + Hindi | 50 tenants, NPS ≥ 40 |
| **M5: AI Launch** | Jun 2027 | 2+ AI features in production | 30% AI adoption |
| **M6: Ecosystem Launch** | Dec 2027 | Mobile apps + API marketplace | 200 tenants, ₹15L MRR |

---

## 13. Roadmap Governance

### 13.1 Review Cadence

| Review | Frequency | Participants | Output |
|--------|-----------|-------------|--------|
| Sprint Review | Bi-weekly | Engineering, Product, QA | Sprint demo, backlog refinement |
| Phase Gate Review | End of each phase | Leadership, Product, Engineering | Go/No-Go for next phase |
| Roadmap Review | Quarterly | Leadership, Product, Sales, CS | Roadmap adjustments |
| KPI Review | Monthly | Leadership, Product, Finance | Metric tracking, corrective actions |

### 13.2 Change Management

- Roadmap changes require Product Owner approval
- Scope additions must identify trade-offs (what is deprioritized)
- Customer-driven requests evaluated against roadmap themes
- Technical debt allocated 20% of each sprint capacity

---

## 14. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | June 2026 | Product Team | Initial roadmap |
