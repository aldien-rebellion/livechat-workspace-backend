from prometheus_client import Counter, Gauge

# Gauge for active WebSocket connections across channels
active_websocket_connections = Gauge(
    "livechat_active_websocket_connections",
    "Current number of active WebSocket connections",
)

# Counter for messages published
chat_messages_published_total = Counter(
    "livechat_messages_published_total",
    "Total number of chat messages published",
    ["message_type"],
)

# Counter for read receipts
chat_messages_read_total = Counter(
    "livechat_messages_read_total",
    "Total number of messages marked as read",
)
