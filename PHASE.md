# Phase 9: Production Monitoring (Prometheus & Grafana)

> **Branch:** `feature/phase-9-monitoring-observability`
> **Master Plan Reference:** `plan.md` (Phase 9, Section 1 & 7)
> **Objective:** Instrument FastAPI with Prometheus metrics, capture real-time WebSocket metrics, and provide pre-configured Grafana dashboards.

---

## 1. Scope & Deliverables

1. **Prometheus Instrumentation (`app/config/metrics.py`):**
   - Expose `/metrics` endpoint using `prometheus-fastapi-instrumentator`.
   - Custom metrics:
     - `livechat_active_websocket_connections`: Gauge tracking current live WebSocket connections.
     - `livechat_messages_published_total`: Counter tracking message volume by message type.
     - `livechat_messages_read_total`: Counter tracking read receipts.
2. **Monitoring Infrastructure (`docker-compose.monitoring.yml`):**
   - Prometheus container with scrape config (`monitoring/prometheus/prometheus.yml`).
   - Grafana container with automated datasource & dashboard provisioning.
3. **Dashboards (`monitoring/grafana/provisioning/dashboards/`):**
   - Live Chat Observability Dashboard (Active WebSocket connections, message throughput, HTTP RPS, p95 latency).

---

## 2. Checklist for AI Agent / Engineer

- [x] Add `prometheus-fastapi-instrumentator` and configure `/metrics` in `app/main.py`
- [x] Connect custom gauges and counters in WebSocket and message handlers
- [x] Create `monitoring/prometheus/prometheus.yml` scrape configuration
- [x] Configure `docker-compose.monitoring.yml` and test Grafana dashboard
