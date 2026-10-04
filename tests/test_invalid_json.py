import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# List of various malformed/invalid JSON payloads
MALFORMED_JSON_PAYLOADS = [
    ("{incomplete_brace", "Unclosed curly brace"),
    ('{"email": }', "Missing value after key"),
    ('{"email": "test@example.com", "username": "test",}', "Trailing comma"),
    ('{"username": "test', "Unterminated string"),
    ("[1, 2,", "Unterminated array"),
    ("Not a JSON string at all", "Plain text without JSON syntax"),
    ("{'single_quotes': 'not_valid_json'}", "Single quotes instead of double quotes"),
    ("true, false", "Multiple root tokens"),
]


@pytest.mark.parametrize("payload, description", MALFORMED_JSON_PAYLOADS)
def test_pydantic_endpoint_rejects_malformed_json_with_400(
    payload: str, description: str
):
    """
    Given a request with Content-Type application/json and malformed JSON body,
    Endpoints using Pydantic models (e.g. /api/v1/auth/register) MUST return
    HTTP 400 Bad Request with a clean error message and not 500 or 422.
    """
    response = client.post(
        "/api/v1/auth/register",
        content=payload,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400, (
        f"Expected 400 for {description}, but got {response.status_code}. "
        f"Response text: {response.text}"
    )
    data = response.json()
    assert data.get("error") == "Bad Request"
    assert "Invalid JSON format" in data.get("detail", "")
    assert "message" in data


@pytest.mark.parametrize("payload, description", MALFORMED_JSON_PAYLOADS)
def test_direct_json_endpoint_rejects_malformed_json_with_400(
    payload: str, description: str
):
    """
    Given a request to /api/v1/auth/login with malformed JSON body,
    The endpoint MUST return HTTP 400 Bad Request with error detail,
    and not raise an unhandled exception or return 500.
    """
    response = client.post(
        "/api/v1/auth/login",
        content=payload,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400, (
        f"Expected 400 for {description}, but got {response.status_code}. "
        f"Response text: {response.text}"
    )
    data = response.json()
    assert "Invalid JSON format" in data.get("detail", "")


def test_login_rejects_non_object_json_with_400():
    """
    If JSON is valid syntax but is an array or primitive instead of a JSON object/dict,
    /api/v1/auth/login should return 400 Bad Request.
    """
    response = client.post(
        "/api/v1/auth/login",
        content="[1, 2, 3]",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    data = response.json()
    assert "expected JSON object" in data.get("detail", "")


def test_valid_json_with_schema_violations_returns_422():
    """
    Ensure we did not break normal Pydantic schema validation:
    A valid JSON format with missing fields or invalid field types
    should return HTTP 422 (Unprocessable Entity), NOT HTTP 400.
    """
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "only_email@example.com"},  # missing username and password
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], list)
    missing_fields = [
        err["loc"][-1] for err in data["detail"] if err.get("type") == "missing"
    ]
    assert "username" in missing_fields
    assert "password" in missing_fields


def test_workspaces_endpoint_rejects_malformed_json_with_400():
    """
    Test another resource endpoint to ensure the global exception handler
    operates across all routers and endpoints.
    """
    response = client.post(
        "/api/v1/workspaces",
        content='{"name": "Broken Lab",',
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data.get("error") == "Bad Request"
    assert "Invalid JSON format" in data.get("detail", "")


def test_devices_endpoint_rejects_malformed_json_with_400():
    """
    Test devices endpoint to verify malformed JSON handling.
    """
    response = client.post(
        "/api/v1/devices/pico-01/commands",
        content="{bad_syntax",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data.get("error") == "Bad Request"
    assert "Invalid JSON format" in data.get("detail", "")
