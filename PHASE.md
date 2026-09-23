# Phase 7: Containerization, CI/CD Pipeline & VPS Docker Compose

> **Branch:** `feature/phase-7-docker-cicd`
> **Master Plan Reference:** `plan.md` (Phase 7, Section 1 & 7)
> **Objective:** Package the entire application stack into production Docker containers and configure GitHub Actions CI/CD for cloud VPS deployment.

---

## 1. Scope & Deliverables

1. **Multi-Stage Production `Dockerfile`:**
   - Base image: `python:3.11-slim`.
   - Security: Run as non-privileged user (`appuser`).
   - Caching: Layer dependencies separately from source code.
   - Volume mount for `/app/uploads` storage.
2. **Production `docker-compose.yml`:**
   - `postgres`: PostgreSQL 15 with volume persistence and healthchecks.
   - `redis`: Redis 7 with AOF persistence and healthchecks.
   - `api`: FastAPI application (replicated/scalable).
   - `nginx`: Reverse proxy handling WebSocket upgrades and routing.
3. **CI/CD Pipeline (`.github/workflows/ci.yml`):**
   - Lint step: `flake8`, `black --check`, `isort --check`.
   - Test step: Spin up Postgres/Redis services and execute `pytest`.
   - Build step: Verify Docker image build passes.

---

## 2. Checklist for AI Agent / Engineer

- [ ] Create production-ready multi-stage `Dockerfile`
- [ ] Configure `docker-compose.yml` with healthchecks and dependencies
- [ ] Configure Nginx reverse proxy configuration (`nginx/nginx.conf`)
- [ ] Implement `.github/workflows/ci.yml` pipeline
- [ ] Validate full stack startup via `docker compose up --build`
