# Phase 9: Production Monitoring (Prometheus & Grafana)

> **Branch:** `feature/phase-9-monitoring-observability`
> **Master Plan Reference:** `plan.md` (Phase 9, Section 1 & 7)
> **Objective:** Instrument FastAPI with Prometheus metrics, capture real-time WebSocket metrics, and provide pre-configured Grafana dashboards.

---

## 1. Scope & Deliverables

1. **Prometheus Instrumentation (`app/core/metrics.py`):**
   - Expose `/metrics` endpoint using `prometheus-fastapi-instrumentator`.
   - Custom metrics:
     - `livechat_active_websocket_connections`: Gauge tracking current live WebSocket connections.
     - `livechat_messages_processed_total`: Counter tracking message volume by channel and message type.
     - `livechat_db_query_duration_seconds`: Histogram tracking database query execution time.
2. **Monitoring Infrastructure (`docker-compose.monitoring.yml`):**
   - Prometheus container with scrape config (`prometheus/prometheus.yml`).
   - Grafana container with automated datasource & dashboard provisioning.
3. **Dashboards (`monitoring/grafana/dashboards/`):**
   - Live Chat Overview Dashboard (Active users, WebSocket connections, msg/sec throughput, p95 API latency, HTTP error rate).

---

## 2. Checklist for AI Agent / Engineer

- [ ] Add `prometheus-fastapi-instrumentator` and configure `/metrics` in `app/main.py`
- [ ] Implement custom gauges and counters in `app/core/metrics.py`
- [ ] Create `prometheus/prometheus.yml` scrape configuration
- [ ] Configure `docker-compose.monitoring.yml` and test Grafana dashboard
