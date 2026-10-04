# pyrefly: ignore [missing-import]
import pytest
from httpx import AsyncClient
import uuid


@pytest.mark.asyncio
async def test_register_user_success(async_client: AsyncClient):
    unique_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "name": "Test User",
        "email": unique_email,
        "password": "StrongPassword123!",
    }

    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == unique_email
    assert data["name"] == "Test User"
    assert data["role"] == "user"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    # Password should NOT be in response
    assert "password" not in data
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(async_client: AsyncClient):
    unique_email = f"dup_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "name": "First User",
        "email": unique_email,
        "password": "Password123!",
    }

    # First registration
    response1 = await async_client.post("/api/v1/auth/register", json=payload)
    assert response1.status_code == 201

    # Second registration with same email
    response2 = await async_client.post("/api/v1/auth/register", json=payload)
    assert response2.status_code == 409
    assert "already registered" in response2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_validation_failure(async_client: AsyncClient):
    # Invalid email and short password
    payload = {
        "name": "A",
        "email": "not-an-email",
        "password": "short",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient):
    unique_email = f"login_{uuid.uuid4().hex[:8]}@example.com"
    password = "CorrectPassword123!"

    # Register first
    await async_client.post(
        "/api/v1/auth/register",
        json={"name": "Login User", "email": unique_email, "password": password},
    )

    # Login
    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": password},
    )
    assert login_response.status_code == 200
    data = login_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == unique_email


@pytest.mark.asyncio
async def test_login_wrong_password(async_client: AsyncClient):
    unique_email = f"wrongpw_{uuid.uuid4().hex[:8]}@example.com"

    await async_client.post(
        "/api/v1/auth/register",
        json={"name": "User", "email": unique_email, "password": "OriginalPassword123!"},
    )

    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": "WrongPassword999!"},
    )
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_user(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent_user_999@example.com", "password": "Password123!"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(async_client: AsyncClient):
    unique_email = f"me_{uuid.uuid4().hex[:8]}@example.com"
    password = "MyPassword123!"

    # Register and login
    await async_client.post(
        "/api/v1/auth/register",
        json={"name": "Me User", "email": unique_email, "password": password},
    )
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": password},
    )
    token = login_res.json()["access_token"]

    # Call /me with Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    me_response = await async_client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    user_data = me_response.json()
    assert user_data["email"] == unique_email
    assert user_data["name"] == "Me User"


@pytest.mark.asyncio
async def test_get_me_unauthorized(async_client: AsyncClient):
    # No header
    response = await async_client.get("/api/v1/auth/me")
    assert response.status_code == 401

    # Invalid token
    response_invalid = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer completely-invalid-jwt-token"},
    )
    assert response_invalid.status_code == 401
