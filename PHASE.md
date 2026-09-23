# Phase 8: High-Concurrency Load Testing (k6)

> **Branch:** `feature/phase-8-load-testing-k6`
> **Master Plan Reference:** `plan.md` (Phase 8, Section 7)
> **Objective:** Author k6 test scripts to simulate up to 10,000 concurrent WebSocket connections and identify system bottlenecks.

---

## 1. Scope & Deliverables

1. **Test Scripts (`tests/load_testing/`):**
   - `ws_stress_test.js`:
     - Test lifecycle: Ramp up from 100 to 1,000 to 5,000+ Virtual Users (VUs).
     - Connect to WebSocket endpoint `/api/v1/ws/channels/{id}` with JWT authentication.
     - Send periodic chat messages and record latency metrics (connection time, message echo latency p95/p99).
   - `http_load_test.js`:
     - Benchmark message history retrieval under continuous query load.
2. **Benchmark Documentation (`docs/load_testing_report.md`):**
   - Maximum sustainable concurrent connections.
   - Resource utilization (CPU, Memory, PostgreSQL Connection Pool, Redis bandwidth).
   - Performance tuning guidelines (Uvicorn worker count, asyncpg pool size, Linux file descriptors).

---

## 2. Checklist for AI Agent / Engineer

- [ ] Implement `ws_stress_test.js` using `k6/ws`
- [ ] Implement `http_load_test.js` using `k6/http`
- [ ] Execute test runs against local/staging environment
- [ ] Record bottleneck analysis and tuning parameters in benchmark report
