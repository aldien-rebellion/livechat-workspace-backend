# Phase 1: Database Entities & Migrations

> **Branch:** `feature/phase-1-database`
> **Master Plan Reference:** `plan.md` (Phase 1, Section 3)
> **Objective:** Define SQLAlchemy 2.0 async models for the Live Chat platform and generate Alembic migrations without breaking legacy workshop tables.

---

## 1. Scope & Deliverables

1. **SQLAlchemy Async Models (`app/models/`):**
   - Update `app/models/user.py`: Add full attributes (`id` UUID, `email`, `username`, `hashed_password`, `full_name`, `avatar_url`, `is_active`, `created_at`, `updated_at`).
   - Create `app/models/workspace.py`: Define `Workspace` and `WorkspaceMember` (role: owner, admin, member).
   - Create `app/models/channel.py`: Define `Channel` (`channel_type`: PUBLIC, PRIVATE, DIRECT_MESSAGE) and `ChannelMember`.
   - Create `app/models/message.py`: Define `Message` (`parent_id` for threads, `message_type`, `file_url`, `is_edited`, `is_deleted`).
   - Create `app/models/message_read.py`: Define `MessageRead` (composite PK: `message_id`, `user_id`, `read_at`).
2. **Metadata Registration (`app/db/base.py`):**
   - Import all models into `app/db/base.py` for Alembic autogeneration.
   - Retain legacy `Telemetry` model to ensure backward compatibility.
3. **Alembic Migration:**
   - Generate revision: `alembic revision --autogenerate -m "add_livechat_models"`
   - Apply migration: `alembic upgrade head`
   - Verify table creation in PostgreSQL (`livechat_db`).

---

## 2. Checklist for AI Agent / Engineer

- [x] Define `User` model updates in `app/models/user.py`
- [x] Implement `Workspace` and `WorkspaceMember` in `app/models/workspace.py`
- [x] Implement `Channel` and `ChannelMember` in `app/models/channel.py`
- [x] Implement `Message` in `app/models/message.py`
- [x] Implement `MessageRead` in `app/models/message_read.py`
- [x] Export all models in `app/models/__init__.py` and import in `app/db/base.py`
- [x] Run `alembic revision --autogenerate -m "add_livechat_models"`
- [x] Run `alembic upgrade head` and verify schema
