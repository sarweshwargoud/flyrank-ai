import time
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def auth_user(client):
    email = f"flyrank_test_{int(time.time())}@gmail.com"
    password = "TestPassword123!"

    # Signup
    signup_res = client.post("/auth/signup", json={"email": email, "password": password})
    assert signup_res.status_code == 201

    # Login
    login_res = client.post("/auth/login", json={"email": email, "password": password})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    return {
        "email": email,
        "password": password,
        "token": token
    }


def test_public_info(client):
    response = client.get("/public/info")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome stranger! This info is public."}


def test_signup_missing_fields(client):
    res_no_pwd = client.post("/auth/signup", json={"email": "nopass@gmail.com", "password": "   "})
    assert res_no_pwd.status_code == 400
    assert "error" in res_no_pwd.json()

    res_no_email = client.post("/auth/signup", json={"email": "", "password": "somepassword"})
    assert res_no_email.status_code == 400
    assert "error" in res_no_email.json()


def test_login_invalid_credentials(client):
    res = client.post("/auth/login", json={"email": "nonexistent@gmail.com", "password": "wrongpassword"})
    assert res.status_code == 401
    assert res.json() == {"error": "Invalid login credentials"}


def test_protected_profile_no_token(client):
    response = client.get("/protected/profile")
    assert response.status_code == 401
    assert response.json() == {"error": "Access token required"}


def test_protected_profile_valid_token(client, auth_user):
    headers = {"Authorization": f"Bearer {auth_user['token']}"}
    response = client.get("/protected/profile", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == auth_user["email"]
    assert "id" in data


def test_protected_profile_tampered_token(client, auth_user):
    tampered = auth_user["token"][:-5] + "XXXXX"
    headers = {"Authorization": f"Bearer {tampered}"}
    response = client.get("/protected/profile", headers=headers)
    assert response.status_code == 401
    assert response.json() == {"error": "Invalid or expired token"}


def test_protected_dashboard_valid_token(client, auth_user):
    headers = {"Authorization": f"Bearer {auth_user['token']}"}
    response = client.get("/protected/dashboard", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["email"] == auth_user["email"]


def test_protected_dashboard_no_token(client):
    response = client.get("/protected/dashboard")
    assert response.status_code == 401
    assert response.json() == {"error": "Access token required"}


def test_logout_valid_token(client, auth_user):
    headers = {"Authorization": f"Bearer {auth_user['token']}"}
    response = client.post("/auth/logout", headers=headers)
    assert response.status_code == 204
    assert response.text == ""
