# Phase 5: Presence Engine, Read Receipts & Status Caching

> **Branch:** `feature/phase-5-presence-read-receipts`
> **Master Plan Reference:** `plan.md` (Phase 5, Section 4.2 & 5.2–5.3)
> **Objective:** Implement online/offline presence tracking with sliding TTL in Redis, and granular per-user message read receipts.

---

## 1. Scope & Deliverables

1. **Presence Engine (`app/services/presence_service.py`):**
   - On connect / heartbeat: Set Redis key `presence:user:{user_id}` (TTL: 60s), add user to `presence:workspace:{workspace_id}:online`.
   - On disconnect / expiry: Remove from workspace online set, publish `presence:update` (offline).
   - Method: `get_online_users(workspace_id)` -> List of online user IDs.
2. **Granular Read Receipts (`app/services/read_receipt_service.py`):**
   - On WebSocket event `message:read`:
     - Insert record into `message_reads` table (`message_id`, `user_id`, `read_at`).
     - Update `last_read_at` on `channel_members`.
     - Broadcast `message:read_update` via Redis Pub/Sub to channel.
3. **Endpoints & Integration:**
   - `GET /api/v1/workspaces/{workspace_id}/online-users`
   - `POST /api/v1/messages/{message_id}/read`
   - `GET /api/v1/messages/{message_id}/readers`

---

## 2. Checklist for AI Agent / Engineer

- [ ] Implement `PresenceService` with Redis sliding TTL
- [ ] Connect presence lifecycle to WebSocket connect / disconnect / heartbeat
- [ ] Implement granular read receipts in DB and WebSocket broadcast
- [ ] Implement endpoints for online users and message readers
