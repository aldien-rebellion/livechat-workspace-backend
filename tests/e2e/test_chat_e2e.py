import socket
import threading
import time
import uuid

import httpx
import pytest
import uvicorn
from playwright.sync_api import sync_playwright


def get_free_port() -> int:
    s = socket.socket()
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture(scope="module")
def live_server():
    port = get_free_port()
    config = uvicorn.Config(
        "app.main:app",
        host="127.0.0.1",
        port=port,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Wait for server to bind and start listening
    for _ in range(50):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                break
        except OSError:
            time.sleep(0.1)
    else:
        raise RuntimeError("Live test server failed to start")

    yield f"http://127.0.0.1:{port}"

    server.should_exit = True
    thread.join(timeout=2.0)


def test_playwright_e2e_two_users_chat(live_server: str):
    """Playwright E2E interactive test suite for two concurrent users.

    Simulates User A and User B chatting in real-time, verifying:
    1. Authentication and WebSocket handshake.
    2. Bidirectional real-time message broadcast.
    3. Typing indicator broadcast.
    4. Read receipt update synchronization.
    """
    suffix = uuid.uuid4().hex[:6]
    user_a_name = f"alice_{suffix}"
    user_b_name = f"bob_{suffix}"
    password = "Password123!"

    # 1. Setup users & workspace via HTTP
    with httpx.Client(base_url=live_server) as client:
        # Register User A
        res_a = client.post(
            "/api/v1/auth/register",
            json={
                "username": user_a_name,
                "email": f"{user_a_name}@example.com",
                "password": password,
            },
        )
        assert res_a.status_code == 201, res_a.text
        assert "id" in res_a.json()

        # Register User B
        res_b = client.post(
            "/api/v1/auth/register",
            json={
                "username": user_b_name,
                "email": f"{user_b_name}@example.com",
                "password": password,
            },
        )
        assert res_b.status_code == 201, res_b.text
        user_b_id = res_b.json()["id"]

        # Login User A to get token for workspace setup
        login_a = client.post(
            "/api/v1/auth/login",
            json={"username": user_a_name, "password": password},
        )
        assert login_a.status_code == 200, login_a.text
        token_a = login_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # Create Workspace
        ws_res = client.post(
            "/api/v1/workspaces",
            json={"name": f"E2E Workspace {suffix}"},
            headers=headers_a,
        )
        assert ws_res.status_code == 201, ws_res.text
        ws_id = ws_res.json()["id"]

        # Add User B to Workspace
        add_b = client.post(
            f"/api/v1/workspaces/{ws_id}/members",
            json={"user_id": user_b_id, "role": "MEMBER"},
            headers=headers_a,
        )
        assert add_b.status_code == 201, add_b.text

        # Fetch general channel
        ch_res = client.get(
            f"/api/v1/workspaces/{ws_id}/channels",
            headers=headers_a,
        )
        assert ch_res.status_code == 200, ch_res.text
        channel_id = ch_res.json()[0]["id"]

        # Add User B to Channel
        add_ch_b = client.post(
            f"/api/v1/channels/{channel_id}/members",
            json={"user_id": user_b_id},
            headers=headers_a,
        )
        assert add_ch_b.status_code == 201, add_ch_b.text

    # 2. Launch 2 isolated Playwright browser contexts
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        context_a = browser.new_context()
        context_b = browser.new_context()

        page_a = context_a.new_page()
        page_b = context_b.new_page()

        # Connect User A
        page_a.goto(f"{live_server}/e2e")
        page_a.fill("#username-input", user_a_name)
        page_a.fill("#password-input", password)
        page_a.click("#login-btn")
        page_a.wait_for_selector("#connect-btn:not([disabled])", timeout=5000)

        page_a.fill("#channel-id-input", channel_id)
        page_a.click("#connect-btn")
        page_a.wait_for_selector("#connection-status.status-connected", timeout=5000)

        # Connect User B
        page_b.goto(f"{live_server}/e2e")
        page_b.fill("#username-input", user_b_name)
        page_b.fill("#password-input", password)
        page_b.click("#login-btn")
        page_b.wait_for_selector("#connect-btn:not([disabled])", timeout=5000)

        page_b.fill("#channel-id-input", channel_id)
        page_b.click("#connect-btn")
        page_b.wait_for_selector("#connection-status.status-connected", timeout=5000)

        # 3. User A sends message to User B
        alice_msg = f"Hello Bob, this is Alice! {suffix}"
        page_a.fill("#message-input", alice_msg)
        page_a.click("#send-btn")

        # Verify User B receives Alice's message in real time
        page_b.wait_for_selector(f".message-item:has-text('{alice_msg}')", timeout=5000)

        # 4. User B sends reply message to User A
        bob_msg = f"Hey Alice, Bob received your message! {suffix}"
        page_b.fill("#message-input", bob_msg)
        page_b.click("#send-btn")

        # Verify User A receives Bob's message in real time
        page_a.wait_for_selector(f".message-item:has-text('{bob_msg}')", timeout=5000)

        # 5. User A triggers Typing Indicator
        page_a.click("#typing-btn")
        # Verify User B sees typing indicator
        page_b.wait_for_selector(
            "#typing-indicator:has-text('is typing...')", timeout=5000
        )

        # 6. User B marks last message as read
        page_b.click("#mark-read-btn")
        # Verify User A receives read receipt update
        page_a.wait_for_selector(
            ".message-item .msg-meta:has-text('Read by')", timeout=5000
        )

        browser.close()
