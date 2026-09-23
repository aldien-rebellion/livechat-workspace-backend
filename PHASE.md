# Phase 6: Automated Testing Suite

> **Branch:** `feature/phase-6-automated-testing`
> **Master Plan Reference:** `plan.md` (Phase 6, Section 7)
> **Objective:** Implement comprehensive async unit and integration tests covering authentication, REST endpoints, WebSocket real-time communication, and Playwright 2-user E2E tests.

---

## 1. Scope & Deliverables

1. **Test Infrastructure & Fixtures (`tests/conftest.py`):**
   - Async SQLAlchemy test session with rollback or isolated test database.
   - Redis test client integration.
   - Authenticated client fixtures.
2. **REST API Tests:**
   - `tests/test_auth.py`: Registration, login with valid/invalid credentials, JWT verification.
   - `tests/test_channels.py`: Workspaces, Group channels, 1-on-1 DM creation, message pagination, file uploads.
   - `tests/test_presence_read_receipts.py`: Presence lifecycle, read receipts, online users endpoint.
3. **WebSocket Real-Time Tests (`tests/test_websocket.py`):**
   - WebSocket connection handshake & token validation.
   - Message send, ACK, and broadcast verification.
   - Read receipt event flow verification.
4. **Playwright E2E Multi-User Interactive Testing (`tests/e2e/`):**
   - `tests/e2e/client.html`: Lightweight HTML/JS chat test client with JWT auth, channel switching, live WebSocket message stream, typing indicator, and read receipt triggers.
   - `tests/e2e/test_chat_e2e.py`: Playwright test script launching 2 isolated browser contexts (User A & User B) to simulate real users chatting simultaneously and verifying real-time synchronization.

---

## 2. Checklist for AI Agent / Engineer

- [x] Configure async test fixtures in `tests/conftest.py`
- [x] Implement Auth test suite in `tests/test_auth.py`
- [x] Implement Workspace & Channel test suite in `tests/test_channels.py`
- [x] Implement WebSocket test suite in `tests/test_websocket.py`
- [ ] Build lightweight HTML chat client in `tests/e2e/client.html`
- [ ] Implement Playwright multi-user E2E tests in `tests/e2e/test_chat_e2e.py`
- [ ] Run `pytest -v` (unit/integration) and verify full test suite passes
