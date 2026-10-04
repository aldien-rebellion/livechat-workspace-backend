# Real-Time Live Chat Workspace Platform (Backend)

> **Enterprise-grade, high-concurrency real-time live chat workspace platform built with FastAPI, PostgreSQL, Redis Pub/Sub, WebSockets, Docker, Prometheus, and Grafana.**

---

## ≡ƒôî Project Overview

This project is a distributed, multi-tenant real-time messaging platform designed for team communication, direct messaging, and workspace collaboration. It utilizes modern async Python patterns (SQLAlchemy 2.0 asyncpg, asyncio) coupled with Redis Pub/Sub for horizontal scalability across multiple server instances, ensuring sub-100ms message delivery, sliding TTL presence tracking, and granular per-message read receipts.

### ≡ƒ¢á∩╕Å Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend Framework** | **FastAPI** (Python 3.11, ASGI, Asyncio) |
| **Database & ORM** | **PostgreSQL 15+**, **SQLAlchemy 2.0** (Async), **Asyncpg**, **Alembic** |
| **Cache & Pub/Sub** | **Redis 7+** (In-memory caching, Sliding TTL Presence, Pub/Sub fanout) |
| **Real-Time Protocol** | **WebSockets** (Bidirectional event-driven messaging, ACK handshakes) |
| **Reverse Proxy** | **Nginx 1.25** (SSL termination, WebSocket connection upgrading, static file serving) |
| **Containerization** | **Docker**, **Docker Compose** (Multi-stage non-root build) |
| **Testing & QA** | **Pytest**, **Httpx**, **Playwright** (2-User interactive E2E), **k6** (High-concurrency stress testing) |
| **Observability** | **Prometheus**, **prometheus-fastapi-instrumentator**, **Grafana** (Auto-provisioned dashboards) |

---

## ≡ƒÅ¢∩╕Å System Architecture

```
                  ΓöîΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÉ
                  Γöé          Clients / Web Browsers          Γöé
                  ΓööΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓö¼ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÿ
                                       Γöé HTTP / WebSockets
                                       Γû╝
                  ΓöîΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÉ
                  Γöé              Nginx Proxy                Γöé
                  Γöé   Port 80/443 (SSL, WS Upgrade, Uploads)Γöé
                  ΓööΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓö¼ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÿ
                                       Γöé
                      ΓöîΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓö┤ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÉ
                      Γû╝                                 Γû╝
         ΓöîΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÉ       ΓöîΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÉ
         Γöé     FastAPI Worker 1    Γöé       Γöé     FastAPI Worker 2    Γöé
         Γöé   (WebSocket / REST)    Γöé       Γöé   (WebSocket / REST)    Γöé
         ΓööΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓö¼ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÿ       ΓööΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓö¼ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÿ
                      Γöé                                 Γöé
           ΓöîΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓö┤ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓö¼ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓö┤ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÉ
           Γû╝                         Γû╝                             Γû╝
ΓöîΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÉ ΓöîΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÉ ΓöîΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÉ
Γöé     PostgreSQL 15     Γöé Γöé     Redis 7 Cache     Γöé Γöé Prometheus & Grafana  Γöé
Γöé  (Persistent Storage) Γöé Γöé (Pub/Sub & Presence)  Γöé Γöé (Metrics & Dashboard) Γöé
ΓööΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÿ ΓööΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÿ ΓööΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÿ
```

---

## Γ£¿ Core Features

1. **Multi-Tenant Workspaces & Channels:**
   - Workspaces with role-based member management (`OWNER`, `ADMIN`, `MEMBER`).
   - Group Channels (`PUBLIC`, `PRIVATE`) with automatic `#general` channel initialization.
   - Idempotent 1-on-1 Direct Messaging (DM) channels.
2. **Real-Time WebSocket Engine:**
   - In-memory `ConnectionManager` mapping active sockets by `channel_id` and `user_id`.
   - Database-first persistence: messages are committed to PostgreSQL before broadcast.
   - Redis Pub/Sub fanout across clustered application instances with sender deduplication.
   - Instant client ACK delivery (`message:ack`).
3. **Presence Engine & Granular Read Receipts:**
   - User online/offline presence tracking via Redis with 60-second sliding TTL heartbeats.
   - Workspace-level online sets and real-time `presence:update` broadcast.
   - Granular per-user read receipt persistence in `message_reads` table and instant `message:read_update` broadcast.
4. **File & Media Storage Service:**
   - Abstracted storage interface with `LocalStorageService`.
   - MIME validation, file size limits (50MB), UUID renaming, and static file serving.
5. **Security & Authentication:**
   - JWT Access tokens (HS256) and refresh tokens with sliding expiration.
   - Secure password hashing using bcrypt.
   - Role-based dependency injection and channel membership authorization.
6. **Production Observability:**
   - Pre-configured `/metrics` endpoint with custom metrics (`livechat_active_websocket_connections`, `livechat_messages_published_total`, `livechat_messages_read_total`).
   - Pre-provisioned Grafana monitoring dashboard.

---

## ≡ƒÜÇ Quick Start Guide

### 1. Prerequisites
- **Python 3.11+**
- **Docker & Docker Compose**
- **Git**

### 2. Local Development Setup

```bash
# 1. Clone the repository
git clone https://github.com/aldien-rebellion/livechat-workspace-backend.git
cd livechat-workspace-backend

# 2. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
pip install playwright pytest-playwright
playwright install chromium

# 4. Start PostgreSQL and Redis via Docker
docker compose up -d postgres redis

# 5. Run database migrations
alembic upgrade head

# 6. Start the development server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## ≡ƒîÉ Application Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/e2e` | `GET` | **Interactive Real-Time Chat Web Client UI** |
| `/api/v1/docs` | `GET` | **Swagger Interactive API Documentation** |
| `/metrics` | `GET` | **Prometheus System & Application Metrics** |
| `/health` | `GET` | Health Check Endpoint |
| `/api/v1/auth/register` | `POST` | User Registration |
| `/api/v1/auth/login` | `POST` | User Authentication (Returns JWT Access & Refresh Token) |
| `/api/v1/workspaces` | `GET / POST` | List & Create Workspaces |
| `/api/v1/workspaces/{id}/channels` | `GET / POST` | List & Create Channels |
| `/api/v1/channels/direct` | `POST` | Idempotent Direct Message Channel Creation |
| `/api/v1/channels/{id}/messages` | `GET` | Paginated Message History |
| `/api/v1/files/upload` | `POST` | Multipart File Upload |
| `/api/v1/ws/channels/{channel_id}` | `WebSocket` | **Bi-directional Real-Time WebSocket Channel** |

---

## ≡ƒº¬ Testing & Verification

The project includes unit tests, integration tests, and Playwright 2-user interactive E2E tests:

```bash
# Run all automated tests (18 tests)
pytest tests/ -v

# Run Playwright E2E interactive test suite (Simulates User A and User B concurrently)
pytest tests/e2e/test_chat_e2e.py -v

# Verify code quality & standards
black --check app tests
isort --check app tests
flake8 app tests
```

### High-Concurrency Load Testing (k6)
Load test scripts and benchmarks are documented in [`docs/load_testing_report.md`](docs/load_testing_report.md):

```bash
# Run HTTP REST load test (up to 100 VUs)
k6 run tests/load_testing/http_load_test.js

# Run WebSocket stress test (50 concurrent sockets)
k6 run tests/load_testing/ws_stress_test.js
```

---

## ≡ƒÉ│ Docker Deployment

### Run Full Production Stack
```bash
docker compose up --build -d
```
Services started:
- `api` (FastAPI ASGI application)
- `postgres` (PostgreSQL 15 database)
- `redis` (Redis 7 with AOF persistence)
- `rabbitmq` (Message broker)
- `nginx` (Reverse proxy on port 80 with WebSocket upgrades)

### Run Monitoring Stack (Prometheus + Grafana)
```bash
docker compose -f docker-compose.monitoring.yml up -d
```
Access points:
- **Grafana Dashboard:** `http://localhost:3000` (User: `admin` / Password: `admin`)
- **Prometheus UI:** `http://localhost:9090`

---

## ≡ƒôä License
This project is developed for educational and academic project submission purposes.


---

# Workshop 12: Cloud Deployment Guide (Terraform + AWS EC2 + GitHub Actions)

> **Stack:** FastAPI · Uvicorn · Docker · Terraform · GitHub Actions · AWS (EC2 Ubuntu 22.04 LTS)

## 📁 Infrastructure & Deployment Structure

```
.
├── .github/
│   └── workflows/
│       ├── ci.yml                  # CI: Lint, Test, Docker build verify
│       └── cd.yml                  # CD: Build→Push (Docker Hub) → Deploy (SSH to AWS EC2)
├── infrastructure/
│   └── main.tf                     # Terraform – provisions AWS EC2 + Security Group
├── docker-compose.prod.yml         # Production stack (runs on cloud server)
├── app/
│   └── main.py                     # +GET /health endpoint
└── tests/
    └── test_health.py              # +test_health_endpoint()
```

## 🚀 Quick Deployment Guide

### Step 1 — Provision the Cloud Server with Terraform
```bash
cd infrastructure/
terraform init
$pubKey = Get-Content "$HOME\.ssh\id_rsa_deploy.pub" -Raw
terraform apply -var="aws_region=ap-southeast-2" -var="instance_type=t3.micro" -var="public_key=$pubKey"
```

### Step 2 — Verify Health Endpoint
```bash
curl http://<PUBLIC_IP>:8000/health
# Response: {"status":"ok","message":"Hello Sakon Nakhon Cloud!"}
```
