import uuid

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_websocket_chat_flow(client: TestClient):
    # 1. Setup user & workspace & channel purely via REST API
    suffix = uuid.uuid4().hex[:6]
    username = f"ws_user_{suffix}"
    email = f"{username}@test.com"
    password = "Password123!"

    # Register
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": password},
    )
    assert reg.status_code == 201, reg.text
    user_id = reg.json()["id"]

    # Login
    login = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create workspace
    ws_res = client.post(
        "/api/v1/workspaces",
        json={"name": "WS Workspace"},
        headers=headers,
    )
    assert ws_res.status_code == 201, ws_res.text
    ws_id = ws_res.json()["id"]

    # Get auto-created #general channel
    chans_res = client.get(f"/api/v1/workspaces/{ws_id}/channels", headers=headers)
    assert chans_res.status_code == 200, chans_res.text
    channel_id = chans_res.json()[0]["id"]

    # 2. Connection with invalid token rejected
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(
            f"/api/v1/ws/channels/{channel_id}?token=invalid_token"
        ):
            pass

    # 3. Connection with valid token accepted
    with client.websocket_connect(
        f"/api/v1/ws/channels/{channel_id}?token={token}"
    ) as ws:
        # Ping / Pong
        ws.send_json({"event": "presence:ping"})
        response = ws.receive_json()
        assert response.get("event") == "presence:pong"

        # Send Message
        ws.send_json(
            {
                "event": "message:send",
                "data": {
                    "content": "Hello real-time WebSocket!",
                },
            }
        )

        # Receive ACK
        ack_res = ws.receive_json()
        assert ack_res.get("event") == "message:ack"
        assert "id" in ack_res.get("data", {})
        msg_id = ack_res["data"]["id"]

        # Receive Broadcast
        bcast_res = ws.receive_json()
        assert bcast_res.get("event") == "message:broadcast"
        assert bcast_res["data"]["id"] == msg_id
        assert bcast_res["data"]["content"] == "Hello real-time WebSocket!"
        assert bcast_res["data"]["user"]["id"] == str(user_id)

        # Test Empty Content Validation (Refactoring Plan Task #104)
        ws.send_json(
            {
                "event": "message:send",
                "data": {
                    "content": "",
                },
            }
        )
        err_res = ws.receive_json()
        assert err_res.get("event") == "error"
        assert "Content cannot be empty" in err_res.get("data", {}).get("message", "")
