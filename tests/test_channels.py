import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def create_authenticated_user(client: AsyncClient, prefix: str = "user"):
    suffix = uuid.uuid4().hex[:8]
    username = f"{prefix}_{suffix}"
    email = f"{username}@test.com"
    password = "Password123!"

    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": password},
    )
    assert reg.status_code == 201, reg.text
    user_id = reg.json()["id"]

    login = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return user_id, headers


@pytest.mark.asyncio
async def test_workspace_and_channel_crud(client: AsyncClient):
    user_id, headers = await create_authenticated_user(client, "ws_owner")

    # 1. Create workspace
    ws_res = await client.post(
        "/api/v1/workspaces",
        json={"name": "Rocket Science Lab"},
        headers=headers,
    )
    assert ws_res.status_code == 201, ws_res.text
    ws_data = ws_res.json()
    ws_id = ws_data["id"]
    assert ws_data["name"] == "Rocket Science Lab"
    assert ws_data["slug"].startswith("rocket-science-lab")

    # 2. List workspaces
    list_ws = await client.get("/api/v1/workspaces", headers=headers)
    assert list_ws.status_code == 200
    assert any(w["id"] == ws_id for w in list_ws.json())

    # 3. List workspace channels (should contain auto-created #general)
    chan_list = await client.get(
        f"/api/v1/workspaces/{ws_id}/channels", headers=headers
    )
    assert chan_list.status_code == 200
    channels = chan_list.json()
    assert any(c["name"] == "general" for c in channels)

    # 4. Create new public channel
    new_chan = await client.post(
        f"/api/v1/workspaces/{ws_id}/channels",
        json={
            "name": "random",
            "topic": "Non-work banter",
            "channel_type": "PUBLIC",
        },
        headers=headers,
    )
    assert new_chan.status_code == 201
    random_chan_id = new_chan.json()["id"]

    # 5. Send message via REST
    msg_res = await client.post(
        f"/api/v1/channels/{random_chan_id}/messages",
        json={"content": "Hello world!"},
        headers=headers,
    )
    assert msg_res.status_code == 201
    msg_data = msg_res.json()
    assert msg_data["content"] == "Hello world!"
    msg_id = msg_data["id"]

    # 6. Get messages
    get_msgs = await client.get(
        f"/api/v1/channels/{random_chan_id}/messages", headers=headers
    )
    assert get_msgs.status_code == 200
    msgs = get_msgs.json()
    assert len(msgs) == 1
    assert msgs[0]["id"] == msg_id

    # 7. Edit message
    edit_res = await client.put(
        f"/api/v1/messages/{msg_id}",
        json={"content": "Updated message content"},
        headers=headers,
    )
    assert edit_res.status_code == 200
    assert edit_res.json()["is_edited"] is True
    assert edit_res.json()["content"] == "Updated message content"

    # 8. Soft delete message
    del_res = await client.delete(f"/api/v1/messages/{msg_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["is_deleted"] is True


@pytest.mark.asyncio
async def test_direct_message_idempotency(client: AsyncClient):
    user_a_id, headers_a = await create_authenticated_user(client, "alice")
    user_b_id, headers_b = await create_authenticated_user(client, "bob")

    # Alice creates DM with Bob
    dm1 = await client.post(
        "/api/v1/channels/direct",
        json={"target_user_id": user_b_id},
        headers=headers_a,
    )
    assert dm1.status_code == 200
    dm1_id = dm1.json()["id"]

    # Bob requests DM with Alice -> Should return existing channel
    dm2 = await client.post(
        "/api/v1/channels/direct",
        json={"target_user_id": user_a_id},
        headers=headers_b,
    )
    assert dm2.status_code == 200
    dm2_id = dm2.json()["id"]

    assert dm1_id == dm2_id


@pytest.mark.asyncio
async def test_file_upload_and_serve(client: AsyncClient):
    _, headers = await create_authenticated_user(client, "file_uploader")

    content = b"This is a test file content for attachment testing."
    files = {"file": ("test_doc.txt", content, "text/plain")}

    # 1. Upload
    up_res = await client.post("/api/v1/files/upload", files=files, headers=headers)
    assert up_res.status_code == 201, up_res.text
    file_info = up_res.json()
    assert "file_id" in file_info
    assert file_info["size"] == len(content)

    # 2. Download / Serve
    file_id = file_info["file_id"]
    down_res = await client.get(f"/api/v1/files/{file_id}")
    assert down_res.status_code == 200
    assert down_res.content == content
