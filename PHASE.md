# Phase 6: Automated Testing Suite

> **Branch:** `feature/phase-6-automated-testing`
> **Master Plan Reference:** `plan.md` (Phase 6, Section 7)
> **Objective:** Implement comprehensive async unit and integration tests covering authentication, REST endpoints, and WebSocket real-time communication.

---

## 1. Scope & Deliverables

1. **Test Infrastructure & Fixtures (`tests/conftest.py`):**
   - Async SQLAlchemy test session with rollback or isolated test database.
   - Mocked/Isolated Redis test client (`fakeredis` or real redis test container).
   - Authenticated client fixtures (`async_client`, `auth_headers`).
2. **REST API Tests:**
   - `tests/test_auth.py`: Registration, login with valid/invalid credentials, JWT verification.
   - `tests/test_workspaces.py`: Workspace creation, membership verification, channel listing.
   - `tests/test_channels.py`: Group channels, 1-on-1 DM creation, message pagination.
3. **WebSocket Real-Time Tests (`tests/test_websocket.py`):**
   - WebSocket connection handshake & token validation.
   - Message send and receive verification.
   - Read receipt event flow verification.
4. **Playwright E2E Multi-User Interactive Testing (`tests/e2e/`):**
   - `tests/e2e/client.html`: Lightweight HTML/JS chat test client with JWT auth, channel switching, live WebSocket message stream, typing indicator, and read receipt triggers.
   - `tests/e2e/test_chat_e2e.py`: Playwright test script launching 2 isolated browser contexts (User A & User B) to simulate real users chatting simultaneously and verifying real-time synchronization.

---

## 2. Checklist for AI Agent / Engineer

- [ ] Configure async test fixtures in `tests/conftest.py`
- [ ] Implement Auth test suite in `tests/test_auth.py`
- [ ] Implement Workspace & Channel test suite in `tests/test_channels.py`
- [ ] Implement WebSocket test suite in `tests/test_websocket.py`
- [ ] Build lightweight HTML chat client in `tests/e2e/client.html`
- [ ] Implement Playwright multi-user E2E tests in `tests/e2e/test_chat_e2e.py`
- [ ] Run `pytest -v` (unit/integration) and `pytest tests/e2e/` (Playwright E2E)
