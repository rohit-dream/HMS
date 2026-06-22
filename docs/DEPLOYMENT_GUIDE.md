# Deployment Guide

## Multi-Tenant Hospital Management SaaS — MVP

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Status** | Active |
| **Companion** | `SDLC Planning/09_MVP_SPRINT_PLAN_V2.md` Appendix E, `docs/SYSTEM_ARCHITECTURE.md` |
| **Primary Region** | `ap-south-1` (Mumbai) |
| **Last Updated** | June 2026 |

---

## 1. Purpose

This guide describes how to run, build, deploy, and operate the Hospital Management SaaS platform across all environments — from a developer laptop through production on AWS. It aligns with Gate G5 (MVP Production Launch) in the sprint plan.

---

## 2. Environments

| Environment | `ENVIRONMENT` value | Purpose | URL pattern |
|-------------|---------------------|---------|-------------|
| **Local** | `development` | Developer workstation; Docker Compose for data services | `http://localhost:8000` (API), `http://localhost:5173` (SPA) |
| **Development** | `development` | Shared dev instance (optional); same config as local with remote DB | `https://dev.platform.com` |
| **Staging** | `staging` | Pre-production UAT, integration tests, load tests | `https://{tenant}.staging.platform.com` |
| **Production** | `production` | Live hospital tenants | `https://{tenant}.platform.com` |

### 2.1 Environment Progression

```mermaid
flowchart LR
    LOCAL["Local<br/>Docker Compose"]
    DEV["Development<br/>Optional shared"]
    STG["Staging<br/>AWS ECS + RDS"]
    PROD["Production<br/>AWS Multi-AZ"]

    LOCAL -->|"Feature complete"| DEV
    DEV -->|"S12 Week 1"| STG
    STG -->|"G5 gate pass"| PROD
```

| Transition | Trigger | Verification |
|------------|---------|--------------|
| Local → Staging | Sprint 12 week 1 | CI green, migrations applied, smoke test |
| Staging → Production | Manual approval after UAT | Full regression, load test, security gate |

---

## 3. Architecture Overview

```mermaid
flowchart TB
    subgraph Clients["Clients"]
        BROWSER["Browser — React SPA"]
    end

    subgraph Edge["Edge Layer"]
        CF["CloudFront CDN<br/>Static assets"]
        NGINX["Nginx Reverse Proxy<br/>TLS · gzip · rate limit"]
        ALB["AWS ALB"]
    end

    subgraph App["Application Layer"]
        API["FastAPI<br/>Uvicorn workers"]
        WORKER["SQS Worker<br/>Email · async jobs"]
    end

    subgraph Data["Data Layer"]
        PG[("PostgreSQL 14<br/>RLS multi-tenant")]
        REDIS[("Redis 7<br/>Cache · rate limit")]
        S3[("S3<br/>Files · reports")]
    end

    BROWSER --> CF
    CF --> NGINX
    NGINX --> ALB
    ALB --> API
    API --> PG
    API --> REDIS
    API --> S3
    WORKER --> PG
    WORKER --> S3
```

### 3.1 Component Responsibilities

| Component | Technology | Responsibility |
|-----------|------------|----------------|
| **Frontend** | React 18, TypeScript, Vite, TailwindCSS | SPA; tenant subdomain routing; calls REST API |
| **API** | FastAPI 0.100+, Python 3.11, Uvicorn | REST `/api/v1/*`, auth, RBAC, business logic |
| **Worker** | Python SQS consumer | Async email, notification delivery, report generation |
| **PostgreSQL** | 14+ with RLS | Primary data store; `tenant_id` row isolation |
| **Redis** | 7+ | Session cache, rate limiting, permission cache |
| **Reverse Proxy** | Nginx 1.24+ | TLS termination, static file serving, request buffering |
| **Object Storage** | Amazon S3 | Patient documents, invoice PDFs, exports |

---

## 4. Local Development

### 4.1 Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Node.js | 20 LTS |
| Docker + Docker Compose | 24+ |
| Git | 2.40+ |

### 4.2 Start Infrastructure

From the repository root:

```bash
docker compose up -d postgres redis
```

Verify services are healthy:

```bash
docker compose ps
docker compose logs postgres --tail 20
docker compose logs redis --tail 20
```

Expected output: both services show `healthy` status.

### 4.3 Backend

```bash
cd backend
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env.local

# Apply database migrations
alembic upgrade head

# Start API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

| Endpoint | URL |
|----------|-----|
| API base | `http://localhost:8000/api/v1` |
| OpenAPI docs | `http://localhost:8000/api/v1/docs` |
| Liveness | `GET http://localhost:8000/api/v1/health` |
| Readiness | `GET http://localhost:8000/api/v1/health/ready` |

### 4.4 Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

App URL: `http://localhost:5173`

### 4.5 Validate Project Structure

```bash
cd backend
python -m scripts.validate_structure
```

---

## 5. Docker Deployment

### 5.1 Current State (Sprint 1)

Sprint 1 uses Docker Compose for **data services only** (PostgreSQL and Redis). Application containers are added in Sprint 12 under `infrastructure/docker/`.

**`docker-compose.yml` services:**

| Service | Image | Port | Volume |
|---------|-------|------|--------|
| `postgres` | `postgres:14-alpine` | 5432 | `postgres_data` |
| `redis` | `redis:7-alpine` | 6379 | — |

### 5.2 Docker Compose Commands

| Action | Command |
|--------|---------|
| Start (detached) | `docker compose up -d` |
| Start with logs | `docker compose up` |
| Stop | `docker compose down` |
| Stop and remove volumes | `docker compose down -v` |
| View logs (all) | `docker compose logs -f` |
| View logs (single service) | `docker compose logs -f postgres` |
| Rebuild (when Dockerfiles exist) | `docker compose build` |
| Rebuild and start | `docker compose up -d --build` |
| Service status | `docker compose ps` |

### 5.3 Planned Application Containers (Sprint 12)

| Image | Dockerfile path | Port |
|-------|-----------------|------|
| `hms-api` | `infrastructure/docker/api/Dockerfile` | 8000 |
| `hms-worker` | `infrastructure/docker/worker/Dockerfile` | — |
| `hms-frontend` | `infrastructure/docker/frontend/Dockerfile` | 80 |
| `hms-nginx` | `infrastructure/docker/nginx/Dockerfile` | 443 |

**Build API image (Sprint 12):**

```bash
docker build -f infrastructure/docker/api/Dockerfile -t hms-api:latest .
```

**Run API container against local Compose DB:**

```bash
docker run --rm -p 8000:8000 \
  --env-file backend/.env.local \
  --network hms_default \
  hms-api:latest
```

### 5.4 Full Stack Compose (Sprint 12)

```bash
# Production-like local stack
docker compose -f docker-compose.yml -f docker-compose.app.yml up -d --build

# View application logs
docker compose -f docker-compose.yml -f docker-compose.app.yml logs -f api
```

---

## 6. Environment Variables

Configuration is loaded by Pydantic `Settings` from environment variables and `backend/.env.local`. Never commit `.env.local` or production secrets to git.

### 6.1 Application Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENVIRONMENT` | Yes | `development` | `development`, `staging`, `production`, or `test` |
| `LOG_LEVEL` | No | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `API_V1_PREFIX` | No | `/api/v1` | API route prefix |
| `CORS_ORIGINS` | Yes (prod) | `http://localhost:5173` | Comma-separated allowed origins; never `*` in production |
| `SKIP_STARTUP_CHECKS` | No | `false` | Set `true` to skip DB/Redis ping on boot (tests only) |

### 6.2 Database Variables

Use **either** `DATABASE_URL` **or** individual `DATABASE_*` variables.

| Variable | Required | Default (local) | Description |
|----------|----------|-----------------|-------------|
| `DATABASE_URL` | Preferred in CI/staging/prod | — | Full PostgreSQL connection string |
| `DATABASE_HOST` | If no URL | `localhost` | PostgreSQL host |
| `DATABASE_PORT` | If no URL | `5432` | PostgreSQL port |
| `DATABASE_NAME` | If no URL | `hms_dev` | Database name |
| `DATABASE_USER` | If no URL | `hms` | Database user |
| `DATABASE_PASSWORD` | If no URL | `hms` | Database password (URL-encode special chars as `%40` for `@`) |
| `DATABASE_POOL_SIZE` | No | `5` | SQLAlchemy pool size |
| `DATABASE_MAX_OVERFLOW` | No | `10` | Pool overflow connections |
| `DATABASE_ECHO` | No | `false` | Log SQL statements (dev only) |

**Local example:**

```env
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=hms_dev
DATABASE_USER=hms
DATABASE_PASSWORD=hms
```

**CI example:**

```env
DATABASE_URL=postgresql://hms:hms@localhost:5432/hms_test
```

### 6.3 Redis Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_URL` | Yes | `redis://localhost:6379/0` | Redis connection URL |
| `REDIS_CONNECT_TIMEOUT_SECONDS` | No | `2` | Connection timeout |

### 6.4 JWT Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JWT_PRIVATE_KEY_PATH` | Yes | `./keys/private.pem` | RS256 private key PEM file path |
| `JWT_PUBLIC_KEY_PATH` | Yes | `./keys/public.pem` | RS256 public key PEM file path |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Access token TTL |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token TTL |
| `JWT_ISSUER` | No | `https://auth.platform.com` | Token `iss` claim |
| `TENANT_BASE_DOMAIN` | Yes | `platform.com` | Base domain for subdomain tenant resolution |
| `AUTH_RATE_LIMIT_PER_MINUTE` | No | `10` | Login/refresh rate limit per IP |

**Generate JWT keys (Sprint 3):**

```bash
cd backend
python scripts/generate_jwt_keys.py
```

Production keys are stored in AWS Secrets Manager, not on disk in containers.

### 6.5 AWS Integration Variables (Sprint 4+)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AWS_REGION` | Staging+ | `ap-south-1` | AWS region |
| `S3_BUCKET` | Staging+ | — | File upload bucket name |
| `SQS_QUEUE_URL` | Staging+ | — | Async job queue URL |
| `SES_FROM_EMAIL` | Staging+ | — | Verified SES sender address |

### 6.6 Payment Variables (Sprint 12)

| Variable | Required | Description |
|----------|----------|-------------|
| `RAZORPAY_KEY_ID` | Production | Razorpay API key |
| `RAZORPAY_KEY_SECRET` | Production | Razorpay API secret |
| `RAZORPAY_WEBHOOK_SECRET` | Production | Webhook signature verification secret |

### 6.7 Frontend Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_BASE_URL` | Yes | `http://localhost:8000/api/v1` | Backend API base URL |
| `VITE_APP_NAME` | No | `HMS Platform` | Application display name |

Copy from `frontend/.env.example` to `frontend/.env.local` for local development.

---

## 7. CI/CD Flow

CI/CD is implemented with GitHub Actions. Full deployment automation is completed in Sprint 12.

```mermaid
flowchart TB
    DEV["Developer push / PR"]
    CI["GitHub Actions CI"]
    LINT["Lint — ruff + eslint"]
    TEST["Test — pytest"]
    BUILD["Build — npm run build"]
    MERGE["Merge to dev"]
    STG_DEPLOY["Deploy to Staging<br/>ECS rolling update"]
    SMOKE["Smoke test"]
    APPROVE["Manual approval"]
    PROD_DEPLOY["Deploy to Production"]
    MONITOR["Monitor 24h"]

    DEV --> CI
    CI --> LINT
    CI --> TEST
    CI --> BUILD
    LINT --> MERGE
    TEST --> MERGE
    BUILD --> MERGE
    MERGE --> STG_DEPLOY
    STG_DEPLOY --> SMOKE
    SMOKE --> APPROVE
    APPROVE --> PROD_DEPLOY
    PROD_DEPLOY --> MONITOR
```

### 7.1 GitHub Actions — Current Pipeline (Sprint 1)

File: `.github/workflows/ci.yml`

| Job | Steps | Working directory |
|-----|-------|-------------------|
| **backend** | Checkout → Python 3.11 → `pip install` → `ruff check .` → `pytest tests/ -v` | `backend/` |
| **frontend** | Checkout → Node 20 → `npm ci` → `npm run lint` → `npm run typecheck` → `npm run build` | `frontend/` |

**Triggers:** push to `main`, `dev`, `rohit/dev`; pull requests to `main`, `dev`.

### 7.2 Planned Pipeline Additions (Sprint 12)

| Stage | Action | Tool |
|-------|--------|------|
| **Test** | Coverage gate, tenant isolation, Bandit SAST | pytest, bandit |
| **Build** | Docker images for API, worker, frontend | `docker build` → ECR |
| **Deploy (staging)** | ECS rolling update, run migrations | Terraform + `scripts/deploy.sh` |
| **Deploy (production)** | Manual workflow dispatch after approval | GitHub Actions `workflow_dispatch` |

### 7.3 Branch Strategy

| Branch | Purpose | Deploy target |
|--------|---------|---------------|
| `main` | Production-ready releases | Production (manual) |
| `dev` | Integration branch | Staging (auto, S12+) |
| `rohit/dev` | Active development | None (CI only) |
| `feature/*` | Feature branches | None (CI on PR) |

### 7.4 Required GitHub Secrets (Sprint 12)

| Secret | Used by |
|--------|---------|
| `AWS_ACCESS_KEY_ID` | ECR push, ECS deploy |
| `AWS_SECRET_ACCESS_KEY` | ECR push, ECS deploy |
| `AWS_REGION` | Deploy workflows |
| `ECR_REPOSITORY_API` | API image push |
| `ECR_REPOSITORY_FRONTEND` | Frontend image push |

Application secrets (database, JWT, Razorpay) are stored in **AWS Secrets Manager**, referenced by ECS task definitions — not in GitHub Secrets.

---

## 8. Database Migration Process

Schema changes are managed exclusively through Alembic migrations in `backend/alembic/versions/`.

### 8.1 Migration Workflow

```mermaid
flowchart LR
    DEV["Write migration<br/>+ RLS policies"]
    LOCAL["alembic upgrade head<br/>on local DB"]
    TEST["pytest integration<br/>tests pass"]
    REVIEW["PR review"]
    STG["Deploy to staging<br/>alembic upgrade head"]
    PROD["Deploy to production<br/>alembic upgrade head"]

    DEV --> LOCAL --> TEST --> REVIEW --> STG --> PROD
```

### 8.2 Commands

| Action | Command | When |
|--------|---------|------|
| Apply all pending migrations | `alembic upgrade head` | Local dev, deploy |
| Apply one step | `alembic upgrade +1` | Debugging |
| Show current revision | `alembic current` | Verify state |
| Show history | `alembic history --verbose` | Audit |
| Generate new migration | `alembic revision -m "description"` | After model change |
| Rollback one revision | `alembic downgrade -1` | Emergency only |

**Always run from `backend/` directory with `DATABASE_URL` or `DATABASE_*` set.**

### 8.3 Migration Rules

| Rule | Rationale |
|------|-----------|
| Never edit a migration that has been applied to staging or production | Breaks revision chain |
| Every tenant-scoped table includes RLS policies in the same migration | Prevents isolation gaps |
| Include `upgrade()` and `downgrade()` functions | Enables controlled rollback |
| Test migrations on a copy of production data before major releases | Catches lock/timeout issues |
| Create RDS manual snapshot before production migration | Recovery point |

### 8.4 Production Migration Execution (Sprint 12)

Migrations run as a one-off ECS task before the rolling deploy:

```bash
# Via infrastructure script
./infrastructure/scripts/migrate.sh staging
./infrastructure/scripts/migrate.sh production
```

The script runs:

```bash
alembic upgrade head
```

against the target environment database using credentials from Secrets Manager.

### 8.5 Rollback Process

| Scenario | Action |
|----------|--------|
| Migration is reversible | `alembic downgrade -1` on affected environment |
| Migration is irreversible (data transform) | Ship a forward-fix migration (`alembic revision`) |
| Critical data corruption | Restore RDS from snapshot (see Section 11) |

**Preference order:** forward-fix migration → application rollback → database restore.

---

## 9. Staging Deployment (Sprint 12)

### 9.1 AWS Services

| Component | AWS Service | Configuration |
|-----------|-------------|---------------|
| API + Worker | ECS Fargate | 2 tasks minimum, auto-scaling |
| Database | RDS PostgreSQL 14 | Single-AZ (staging), encrypted |
| Cache | ElastiCache Redis 7 | Single node |
| Files | S3 | Versioning enabled |
| Secrets | Secrets Manager | All credentials |
| TLS | ACM + ALB | `*.staging.platform.com` |
| DNS | Route 53 | Wildcard subdomain |
| Monitoring | CloudWatch | Logs, metrics, alarms |
| Email | SES | Sandbox → production access |

**Terraform roots:** `infrastructure/terraform/staging/`

### 9.2 Deploy Steps

1. Verify CI is green on the release commit
2. Build and push Docker images to ECR
3. `terraform apply` in `infrastructure/terraform/staging/` (if infra changed)
4. Run `infrastructure/scripts/migrate.sh staging`
5. ECS rolling deploy (new task definition revision)
6. Run `infrastructure/scripts/smoke-test.sh staging`
7. Verify CloudWatch alarms are green

---

## 10. Production Deployment (Sprint 12 — Gate G5)

### 10.1 AWS Services

| Component | AWS Service | Configuration |
|-----------|-------------|---------------|
| API | ECS Fargate | Min 2 tasks, Multi-AZ |
| Worker | ECS Fargate | Min 1 task |
| Database | RDS PostgreSQL 14 | Multi-AZ, automated backups |
| Cache | ElastiCache Redis 7 | Replication group |
| CDN | CloudFront | Static assets + edge caching |
| WAF | AWS WAF | OWASP managed rules on ALB |

**Terraform roots:** `infrastructure/terraform/production/`

### 10.2 Production Deploy Steps

1. Verify CI green on release tag
2. Create RDS manual snapshot (`pre-release-YYYY-MM-DD`)
3. `terraform apply` in `infrastructure/terraform/production/` (if infra changed)
4. Build and push versioned Docker images to ECR (`:v1.0.0` + `:latest`)
5. Run `infrastructure/scripts/migrate.sh production`
6. ECS rolling deploy with minimum healthy 100%, maximum 200%
7. Run `infrastructure/scripts/smoke-test.sh production`
8. Verify CloudWatch alarms and Sentry error rate
9. Monitor for 24 hours before announcing availability

### 10.3 Production Checklist

#### Security

- [ ] HTTPS enforced on all endpoints (HTTP redirects to HTTPS)
- [ ] TLS 1.2+ only; strong cipher suites via ALB policy
- [ ] JWT keys in Secrets Manager; RS256 only
- [ ] CORS restricted to known frontend origins (no wildcard)
- [ ] Security headers middleware active (HSTS, CSP, X-Frame-Options)
- [ ] Rate limiting on auth endpoints via Redis
- [ ] CAPTCHA on public registration
- [ ] 2FA enforced for `hospital_owner` role
- [ ] RLS enabled on all tenant-scoped tables
- [ ] Cross-tenant isolation test passes in CI
- [ ] Bandit SAST — zero high severity findings
- [ ] OWASP ZAP baseline scan — no high findings
- [ ] Secrets not present in git, logs, or error responses
- [ ] IAM least-privilege for ECS task roles

#### Data & Backups

- [ ] RDS automated backups enabled (30-day retention)
- [ ] RDS Multi-AZ enabled
- [ ] Point-in-time recovery enabled
- [ ] S3 versioning enabled on file bucket
- [ ] Backup restore drill completed on staging (monthly)

#### Operations

- [ ] Health checks configured on ALB (`/api/v1/health`, `/api/v1/health/ready`)
- [ ] CloudWatch alarms: 5xx rate, P95 latency, RDS CPU, connection count
- [ ] Structured JSON logging with `request_id` and `tenant_id`
- [ ] Sentry error tracking connected
- [ ] Log retention policy set (90 days application, 1 year audit)
- [ ] On-call escalation documented
- [ ] Incident response runbook accessible to operator

#### Application

- [ ] All Alembic migrations applied
- [ ] System tenant and subscription plans seeded
- [ ] Razorpay webhook URL registered and verified
- [ ] SES domain verified and out of sandbox
- [ ] Smoke test script passes
- [ ] 10 beta tenants onboarded successfully
- [ ] E2E critical journeys pass on production-like staging

---

## 11. Rollback Strategy

### 11.1 Application Rollback

| Step | Action | Time estimate |
|------|--------|---------------|
| 1 | Identify last known-good ECS task definition revision | 5 min |
| 2 | Update ECS service to previous task definition | 5 min |
| 3 | Wait for rolling deploy to stabilize | 10–15 min |
| 4 | Run smoke test against rolled-back version | 5 min |
| 5 | If DB migration caused issue, apply forward-fix or restore DB | Variable |

```bash
# ECS rollback via AWS CLI
aws ecs update-service \
  --cluster hms-production \
  --service hms-api \
  --task-definition hms-api:<previous-revision>
```

### 11.2 Database Rollback

| Method | When to use | Risk |
|--------|-------------|------|
| `alembic downgrade -1` | Reversible migration, no data loss | Low |
| Forward-fix migration | Irreversible schema change with bad data | Medium |
| RDS snapshot restore | Critical corruption or failed migration | High — downtime |

### 11.3 DNS Rollback

If ALB or CloudFront distribution changes cause outage:

1. Revert Route 53 record to previous ALB/distribution ARN
2. TTL is 60 seconds for staging, 300 seconds for production
3. Verify with `dig {tenant}.platform.com`

### 11.4 Rollback Decision Matrix

| Symptom | Rollback layer |
|---------|----------------|
| 5xx spike after deploy, no schema change | Application (ECS) |
| Bug in new migration | Forward-fix or `alembic downgrade` |
| Data corruption | RDS snapshot restore |
| TLS/certificate issue | ACM + ALB listener revert |

---

## 12. Disaster Recovery

### 12.1 Recovery Objectives

| Metric | Target | Source |
|--------|--------|--------|
| **RTO** (Recovery Time Objective) | 4 hours | NFR-AVAIL |
| **RPO** (Recovery Point Objective) | 1 hour | RDS PITR |

### 12.2 Backup Schedule

| Asset | Method | Frequency | Retention |
|-------|--------|-----------|-----------|
| RDS database | Automated snapshot | Daily | 30 days |
| RDS database | Point-in-time recovery | Continuous | 30 days |
| RDS database | Manual pre-release snapshot | On demand | 90 days |
| S3 files | Versioning + lifecycle | Continuous | Per lifecycle policy |
| Terraform state | S3 backend with versioning | On every apply | 90 days |
| JWT keys | Secrets Manager with rotation | On rotation schedule | Previous version retained |

### 12.3 Recovery Procedures

#### Database failure (RDS)

1. Confirm outage via CloudWatch RDS metrics and health checks
2. If Multi-AZ failover did not auto-trigger, initiate manual failover
3. If instance is unrecoverable, restore from latest automated snapshot to a new instance
4. Update Secrets Manager `DATABASE_URL` if endpoint changes
5. Restart ECS tasks to pick up new connection string
6. Run smoke test

#### Region failure (DR)

Primary region: `ap-south-1`. DR strategy for MVP:

1. Restore latest RDS snapshot to DR region RDS instance
2. Replicate S3 bucket cross-region (lifecycle policy, Sprint 12)
3. Deploy ECS stack in DR region from same ECR images
4. Update Route 53 failover routing policy
5. RTO estimate: 4 hours with runbook execution

#### Application data corruption

1. Stop write traffic (set ECS desired count to 0 or enable maintenance mode)
2. Identify corruption scope and timestamp
3. Restore RDS to point-in-time before corruption
4. Replay legitimate transactions if needed
5. Resume traffic after smoke test

### 12.4 DR Drill Schedule

| Drill | Frequency | Environment |
|-------|-----------|-------------|
| RDS snapshot restore | Monthly | Staging |
| Secrets rotation verification | Quarterly | Staging |
| Full failover simulation | Annually | Staging |

---

## 13. Monitoring & Health Checks

### 13.1 Health Endpoints

| Endpoint | Purpose | ALB check |
|----------|---------|-----------|
| `GET /api/v1/health` | Liveness — process is running | Yes |
| `GET /api/v1/health/ready` | Readiness — DB + Redis connectivity | Yes |

Readiness returns `503` when database or Redis is unreachable. ALB should drain unhealthy tasks.

### 13.2 CloudWatch Alarms

| Alarm | Threshold | Action |
|-------|-----------|--------|
| ALB 5xx rate | > 1% for 5 minutes | Page on-call |
| API P95 latency | > 500ms for 5 minutes | Notify team |
| RDS CPU | > 75% for 10 minutes | Notify team |
| RDS connections | > 80% of max | Notify team |
| ECS healthy tasks | < 2 | Page on-call |
| DLQ message count | > 0 for 15 minutes | Notify team |

### 13.3 Logging

| Log type | Format | Destination |
|----------|--------|-------------|
| Application | Structured JSON (`request_id`, `tenant_id`, `level`, `message`) | CloudWatch Logs |
| ALB access | AWS default | S3 + CloudWatch |
| RDS | PostgreSQL slow query log | CloudWatch |
| Audit | `audit.audit_logs` table | PostgreSQL + export |

---

## 14. Smoke Test Checklist

Run after every staging and production deploy via `infrastructure/scripts/smoke-test.sh`:

- [ ] `GET /api/v1/health` returns `200` with `data.status = "ok"`
- [ ] `GET /api/v1/health/ready` returns `200` with `checks.database = "ok"` and `checks.redis = "ok"`
- [ ] Login as test tenant admin succeeds
- [ ] `GET /api/v1/auth/me` returns user profile
- [ ] Create patient record succeeds
- [ ] Book appointment succeeds
- [ ] Cross-tenant isolation spot check returns `404` (not `403`)
- [ ] Frontend loads at tenant subdomain over HTTPS

---

## 15. Future Cloud Deployment Plan

MVP production targets **AWS** in `ap-south-1`. Azure and GCP are documented for future portability.

### 15.1 AWS (Primary — MVP)

| Layer | AWS Service | Notes |
|-------|-------------|-------|
| Compute | ECS Fargate | MVP default; EKS if scale requires |
| Database | RDS PostgreSQL 14 Multi-AZ | RLS requires PostgreSQL |
| Cache | ElastiCache Redis 7 | Auth rate limit, permission cache |
| Storage | S3 | Patient documents, PDFs |
| Queue | SQS | Email and async jobs |
| CDN | CloudFront | Frontend static assets |
| DNS | Route 53 | Wildcard `*.platform.com` |
| Secrets | Secrets Manager | JWT keys, DB credentials, Razorpay |
| Email | SES | Transactional email |
| Monitoring | CloudWatch + Sentry | Logs, metrics, errors |
| WAF | AWS WAF | OWASP rules on ALB |

**IaC layout:**

```
infrastructure/
├── docker/           # Dockerfiles
├── terraform/
│   ├── modules/      # Reusable: vpc, rds, ecs, redis, s3
│   ├── staging/
│   └── production/
└── scripts/          # deploy.sh, migrate.sh, smoke-test.sh, backup.sh
```

### 15.2 Azure (Future)

| AWS | Azure equivalent |
|-----|------------------|
| ECS Fargate | Azure Container Apps |
| RDS PostgreSQL | Azure Database for PostgreSQL Flexible Server |
| ElastiCache | Azure Cache for Redis |
| S3 | Azure Blob Storage |
| SQS | Azure Service Bus |
| CloudFront | Azure Front Door |
| Route 53 | Azure DNS |
| Secrets Manager | Azure Key Vault |
| SES | Azure Communication Services Email |

Migration path: containerize with existing Dockerfiles; replace Terraform modules with Azure Bicep equivalents; update adapter configuration for Blob Storage and Service Bus.

### 15.3 GCP (Future)

| AWS | GCP equivalent |
|-----|----------------|
| ECS Fargate | Cloud Run |
| RDS PostgreSQL | Cloud SQL for PostgreSQL |
| ElastiCache | Memorystore for Redis |
| S3 | Cloud Storage |
| SQS | Cloud Pub/Sub |
| CloudFront | Cloud CDN |
| Route 53 | Cloud DNS |
| Secrets Manager | Secret Manager |
| SES | SendGrid or Gmail API via adapter |

Migration path: Cloud Run deploys from the same container images; Cloud SQL supports PostgreSQL RLS; IAM service accounts replace ECS task roles.

### 15.4 Cloud Selection Criteria

| Criterion | AWS | Azure | GCP |
|-----------|-----|-------|-----|
| India region availability | `ap-south-1` | `centralindia` | `asia-south1` |
| Managed PostgreSQL + RLS | RDS | Flexible Server | Cloud SQL |
| MVP team familiarity | Primary | Secondary | Secondary |
| HIPAA-ready BAA | Available | Available | Available |

---

## 16. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | June 2026 | Initial production guide — MVP-010 Sprint 1 deliverable |
