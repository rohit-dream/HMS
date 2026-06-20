# Infrastructure

AWS deployment assets: containers, Terraform, operational scripts.

## Layout

- `docker/` — Image definitions for API, worker, frontend, nginx
- `terraform/` — IaC modules and environment roots (`staging`, `production`)
- `scripts/` — Deploy, migrate, backup, smoke-test scripts

See [docs/PROJECT_STRUCTURE.md](../docs/PROJECT_STRUCTURE.md) §6.
