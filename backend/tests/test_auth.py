import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from backend.app.database.init_db import init_db
from backend.app.main import app


@pytest.mark.asyncio
async def test_register_user_success():
    await init_db()
    uid = uuid.uuid4().hex[:8]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "email": f"trader_{uid}@tradebot.in",
            "full_name": "Arjun Sharma",
            "password": "strongPassword123!",
        }
        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == f"trader_{uid}@tradebot.in"
        assert data["user"]["full_name"] == "Arjun Sharma"
        assert data["user"]["role"] == "trader"


@pytest.mark.asyncio
async def test_register_duplicate_email():
    await init_db()
    uid = uuid.uuid4().hex[:8]
    email = f"duplicate_{uid}@tradebot.in"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "email": email,
            "full_name": "Duplicate User",
            "password": "password123",
        }
        res1 = await client.post("/api/v1/auth/register", json=payload)
        assert res1.status_code == 201

        # Second registration with same email should fail with 400
        res2 = await client.post("/api/v1/auth/register", json=payload)
        assert res2.status_code == 400
        assert "already exists" in res2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_success():
    await init_db()
    uid = uuid.uuid4().hex[:8]
    email = f"login_{uid}@tradebot.in"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register a user first
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "full_name": "Login Tester",
                "password": "mypassword456",
            },
        )

        # Login
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "mypassword456"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == email


@pytest.mark.asyncio
async def test_login_invalid_password():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "demo@tradebot.in", "password": "wrongpassword!"},
        )
        assert response.status_code == 401
        assert "invalid email or password" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_user():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": f"nonexistent_{uuid.uuid4().hex[:8]}@tradebot.in", "password": "anyPassword"},
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated():
    await init_db()
    uid = uuid.uuid4().hex[:8]
    email = f"profile_{uid}@tradebot.in"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        reg_res = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "full_name": "Profile User",
                "password": "securepwd123",
            },
        )
        token = reg_res.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        me_res = await client.get("/api/v1/auth/me", headers=headers)
        assert me_res.status_code == 200
        data = me_res.json()
        assert data["email"] == email
        assert data["full_name"] == "Profile User"
        assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_me_unauthorized():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        me_res = await client.get("/api/v1/auth/me")
        assert me_res.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = {"Authorization": "Bearer invalid.token.value"}
        me_res = await client.get("/api/v1/auth/me", headers=headers)
        assert me_res.status_code == 401


@pytest.mark.asyncio
async def test_seeded_demo_user_can_login():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "demo@tradebot.in", "password": "password123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "demo@tradebot.in"
        assert data["user"]["role"] == "trader"
