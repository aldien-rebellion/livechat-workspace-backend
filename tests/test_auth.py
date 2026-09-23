import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def test_password_hashing():
    pwd = "secretpassword123"
    hashed = get_password_hash(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_jwt_tokens():
    user_id = str(uuid.uuid4())
    access_token = create_access_token(subject=user_id, role="member")
    refresh_token = create_refresh_token(subject=user_id)

    access_payload = decode_token(access_token)
    assert access_payload["sub"] == user_id
    assert access_payload["type"] == "access"
    assert access_payload["role"] == "member"

    refresh_payload = decode_token(refresh_token)
    assert refresh_payload["sub"] == user_id
    assert refresh_payload["type"] == "refresh"


@pytest.mark.asyncio
async def test_auth_full_flow(client: AsyncClient):
    unique_suffix = uuid.uuid4().hex[:8]
    email = f"user_{unique_suffix}@example.com"
    username = f"user_{unique_suffix}"
    password = "SuperSecurePassword123!"

    # 1. Register
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": username,
            "password": password,
            "full_name": "Test User",
        },
    )
    assert reg_response.status_code == 201, reg_response.text
    user_data = reg_response.json()
    assert user_data["email"] == email
    assert user_data["username"] == username
    assert "id" in user_data

    # 2. Register Duplicate Email / Username
    dup_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": username,
            "password": password,
        },
    )
    assert dup_response.status_code == 400

    # 3. Login with wrong password
    bad_login = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "wrong_password"},
    )
    assert bad_login.status_code == 401

    # 4. Login with correct password (JSON)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]

    # 4b. Login with OAuth2 form data
    form_login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert form_login_response.status_code == 200
    assert "access_token" in form_login_response.json()

    # 5. Get current user profile (/me)
    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["username"] == username
    assert me_data["email"] == email

    # 6. Unauthorized access to /me
    unauth_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert unauth_response.status_code == 401

    # 7. Refresh token
    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 200
    new_tokens = refresh_response.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
