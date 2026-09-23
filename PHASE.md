# Phase 4: Core Real-Time WebSocket & Redis Pub/Sub

> **Branch:** `feature/phase-4-websocket-pubsub`
> **Master Plan Reference:** `plan.md` (Phase 4, Section 4.1 & 5)
> **Objective:** Build the real-time WebSocket connection manager and Redis Pub/Sub bridge to enable multi-instance broadcast and reliable message delivery.

---

## 1. Scope & Deliverables

1. **Connection Manager (`app/services/connection_manager.py`):**
   - Manage local WebSocket connections indexed by `channel_id` and `user_id`.
   - Methods: `connect(websocket, channel_id, user_id)`, `disconnect(websocket, channel_id, user_id)`, `broadcast_to_channel(channel_id, message)`.
2. **Redis Pub/Sub Fanout (`app/services/redis_pubsub.py`):**
   - Async background listener subscribed to Redis channel patterns (`pubsub:channel:*`).
   - Forward Redis broadcast payloads to local `ConnectionManager.broadcast_to_channel()`.
   - Method: `publish_to_channel(channel_id, event_dict)`.
3. **WebSocket Controller (`app/controllers/chat_websocket_controller.py`):**
   - Endpoint: `/api/v1/ws/channels/{channel_id}`
   - Authentication via query param `?token=` or Authorization header.
   - Message Persistence First:
     - On `message:send`: Validate member -> Commit to PostgreSQL -> Publish to Redis Pub/Sub -> Send ACK to sender.
   - Typing indicator forwarding (`typing:start` -> Redis Pub/Sub).

---

## 2. Checklist for AI Agent / Engineer

- [x] Implement `ConnectionManager` for in-memory WebSocket tracking
- [x] Implement `RedisPubSubManager` for cross-instance message sync
- [x] Implement `/api/v1/ws/channels/{channel_id}` endpoint
- [x] Implement strict "Persist to DB first, then Pub/Sub" workflow
- [x] Handle connection lifecycle, heartbeat pings, and disconnects gracefully
