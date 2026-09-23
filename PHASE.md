# Phase 2: Security, Authentication & User Management

> **Branch:** `feature/phase-2-auth-security`
> **Master Plan Reference:** `plan.md` (Phase 2, Section 2 & 6.1)
> **Objective:** Implement production-grade JWT authentication, OAuth2 password flow, user registration, and request auth dependencies.

---

## 1. Scope & Deliverables

1. **Security Utilities (`app/services/security.py`):**
   - Password hashing and verification using `passlib[bcrypt]`.
   - JWT access token and refresh token generation using `python-jose`.
2. **Pydantic Schemas (`app/schemas/user.py`):**
   - `UserCreate` (email, username, password, full_name).
   - `UserResponse` (id, email, username, full_name, avatar_url, is_active, created_at).
   - `Token` (access_token, refresh_token, token_type).
   - `TokenPayload` (sub, exp, type).
3. **Authentication Dependencies (`app/routes/deps.py`):**
   - OAuth2 Password Bearer scheme (`tokenUrl="/api/v1/auth/login"`).
   - `get_current_user`: Decode token, lookup active user in PostgreSQL.
   - `get_current_active_user`: Enforce active status check.
4. **Controllers & Endpoints (`app/controllers/auth_controller.py`):**
   - `POST /api/v1/auth/register`
   - `POST /api/v1/auth/login`
   - `POST /api/v1/auth/refresh`
   - `GET /api/v1/auth/me`

---

## 2. Checklist for AI Agent / Engineer

- [ ] Verify password hashing and JWT token generator in `app/services/security.py`
- [ ] Implement schemas in `app/schemas/user.py`
- [ ] Implement `get_current_user` and `get_current_active_user` in `app/routes/deps.py`
- [ ] Implement endpoints in `app/controllers/auth_controller.py`
- [ ] Add unit tests for registration, login, and auth validation
