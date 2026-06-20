# Hospital Management SaaS

Multi-tenant hospital management platform — monorepo.

## Structure

| Folder | Purpose |
|--------|---------|
| `backend/` | FastAPI API, SQS worker, Alembic migrations |
| `frontend/` | React TypeScript SPA |
| `database/` | PostgreSQL baseline DDL, RLS, seeds |
| `infrastructure/` | Docker, Terraform, deploy scripts |
| `docs/` | Architecture and product documentation |

See [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) for the frozen folder layout.

## Prerequisites

- Python 3.11+
- Node.js 20 LTS
- Docker + Docker Compose

## Quick start

### 1. Infrastructure

```bash
docker compose up -d postgres redis
```

### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env.local
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/api/v1/docs

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

App: http://localhost:5173

### 4. Validate project structure

```bash
cd backend
python -m scripts.validate_structure
```

## Health checks

- Liveness: `GET http://localhost:8000/api/v1/health`
- Readiness: `GET http://localhost:8000/api/v1/health/ready`

## Documentation

- [Development sequence](docs/DEVELOPMENT_SEQUENCE.md)
- [Backend Sprint 1 guide](docs/BACKEND_SPRINT1_EXECUTION.md)
- [Frontend Sprint 1 guide](docs/FRONTEND_SPRINT1_EXECUTION.md)
