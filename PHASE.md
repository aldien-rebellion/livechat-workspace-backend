# Phase 3: Workspace, Channel (Group & DM) & Storage Services

> **Branch:** `feature/phase-3-channels-storage`
> **Master Plan Reference:** `plan.md` (Phase 3, Section 3.1 & 6.2–6.4)
> **Objective:** Implement CRUD services and endpoints for Workspaces, Channels (Public, Private, 1-on-1 DM), and Local Storage for attachments.

---

## 1. Scope & Deliverables

1. **Storage Service Interface (`app/services/storage/`):**
   - Base `StorageService` interface (`upload_file`, `get_file_path`, `delete_file`).
   - `LocalStorageService`: Store binary attachments into `/app/uploads` (or `uploads/`), generate local URL.
2. **Workspace & Channel Services (`app/services/`):**
   - `WorkspaceService`: Create workspace, invite/add members, list user workspaces, check permissions.
   - `ChannelService`:
     - Create and manage Public / Private group channels.
     - Get or create Direct Message (DM) channels between 2 users (`channel_type="DIRECT_MESSAGE"`).
     - Membership management and authorization checks.
3. **Controllers & Endpoints:**
   - `app/controllers/workspace_controller.py`:
     - `POST /api/v1/workspaces`
     - `GET /api/v1/workspaces`
     - `POST /api/v1/workspaces/{id}/channels`
     - `GET /api/v1/workspaces/{id}/channels`
   - `app/controllers/channel_controller.py`:
     - `POST /api/v1/channels/direct` (Get or create 1-on-1 DM)
     - `POST /api/v1/channels/{id}/members`
     - `GET /api/v1/channels/{id}/messages` (Cursor-based pagination)
   - `app/controllers/file_controller.py`:
     - `POST /api/v1/files/upload`
     - `GET /api/v1/files/{file_id}`

---

## 2. Checklist for AI Agent / Engineer

- [x] Implement `StorageService` and `LocalStorageService`
- [x] Implement Pydantic schemas in `app/schemas/workspace.py` and `app/schemas/channel.py`
- [x] Implement `WorkspaceService` with role permissions
- [x] Implement `ChannelService` with Group Channel and 1-on-1 DM support
- [x] Implement REST endpoints in controllers and register in `api_router.py`
