# FlyRank Week 4 — Auth: Login & Protect (FastAPI + Supabase Auth)

## 📌 Project Overview

This project implements robust user authentication and route protection using **FastAPI** and **Supabase Auth** as the managed Identity Provider (IdP).

Instead of storing passwords, managing database credential tables, or implementing custom cryptography in our application, identity management is delegated entirely to Supabase. Our FastAPI service communicates with Supabase over HTTPS, receives cryptographically signed JWT access tokens, validates bearer tokens using a reusable dependency, and secures endpoints.

---

## 🧠 Core Engineering Concepts

### 1. Identity Provider (IdP) & Supabase Auth
* **What it is**: An external service that creates, stores, and verifies user identities.
* **Why we use it**: Passwords are liability. Managing password hashing (e.g. bcrypt/argon2), salt generation, password resets, rate limiting, and credential storage introduces severe attack surfaces. Supabase handles credential management and issues industry-standard signed JWT tokens.

### 2. JSON Web Tokens (JWT) & Bearer Authentication
* **JWT Structure**: A signed token consisting of three base64url segments: `Header.Payload.Signature`.
  * **Header**: Specifies the cryptographic algorithm (e.g., ES256 / HS256).
  * **Payload (Claims)**: Contains standard claims such as `sub` (user ID), `iss` (issuer), `exp` (expiration timestamp), and `email`.
  * **Signature**: Generated using the Identity Provider's private key. If any character in the header or payload is modified, signature verification fails immediately.
* **Bearer Token**: Sent in the standard HTTP header:
  ```http
  Authorization: Bearer <access_token>
  ```
  Whoever "bears" (presents) the valid token is authenticated.

### 3. Access Token vs. Refresh Token
* **Access Token**: Short-lived JWT (Supabase default: 1 hour) used on every API call to authenticate requests.
* **Refresh Token**: Long-lived credential used exclusively to request fresh access tokens without requiring the user to re-type their password.

### 4. Authentication vs. Authorization (401 vs. 403)
* **401 Unauthorized**: *"Who are you?"* The client provided no token, a malformed token, an expired token, or invalid credentials.
* **403 Forbidden**: *"I know who you are, but you do not have permission."* The client identity is verified, but their role/scope lacks access to the requested resource.

### 5. FastAPI Dependencies (`Depends`) & `HTTPBearer`
* **Reusable Dependency (`get_current_user`)**: Centralizes bearer token extraction and Supabase verification in one location. Prevents code duplication and ensures all protected routes share the same security posture.
* **`HTTPBearer` Scheme**: Configures OpenAPI security schemes so that Swagger UI (`/docs`) displays an interactive **Authorize** padlock button.

---

## 🛠️ Technology Stack

* **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
* **Identity Provider**: [Supabase Auth](https://supabase.com/docs/guides/auth)
* **Supabase Python SDK**: `supabase>=2.31.0`
* **Server**: [Uvicorn](https://www.uvicorn.org/)
* **Configuration**: `python-dotenv`
* **Validation**: `pydantic`
* **Testing**: `pytest`, `httpx`

---

## 🚀 Quick Start Guide

### 1. Clone & Setup Environment
Copy the example environment file:
```bash
# On Linux / macOS:
cp .env.example .env

# On Windows (PowerShell):
copy .env.example .env
```

### 2. Configure Supabase Credentials in `.env`
Populate your `.env` file with your project URL and anon public key:
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_anon_key_here
PORT=8000
```
> ⚠️ **Security Warning**: The `.env` file is strictly ignored by `.gitignore`. Never commit real keys or passwords to version control.

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the API Server
```bash
uvicorn app.main:app --reload --port 8000
```
The server will start at **`http://localhost:8000`**  
Interactive Swagger API documentation will be available at **`http://localhost:8000/docs`**

---

## 📋 API Endpoints Reference

| Method | Endpoint | Description | Auth Required | Success Status | Error Statuses |
|---|---|---|:---:|:---:|:---:|
| `POST` | `/auth/signup` | Registers a new user with email & password | ❌ Public | `201 Created` | `400 Bad Request` |
| `POST` | `/auth/login` | Authenticates user; returns JWT access & refresh tokens | ❌ Public | `200 OK` | `400 Bad Request`, `401 Unauthorized` |
| `POST` | `/auth/logout` | Terminates user session | ✅ Bearer JWT | `204 No Content` | `401 Unauthorized` |
| `GET` | `/protected/profile` | Returns authenticated user profile metadata | ✅ Bearer JWT | `200 OK` | `401 Unauthorized` |
| `GET` | `/protected/dashboard`| Second protected endpoint using reusable dependency | ✅ Bearer JWT | `200 OK` | `401 Unauthorized` |
| `GET` | `/public/info` | Public information endpoint | ❌ Public | `200 OK` | — |
| `GET` | `/health` | API & Supabase health status | ❌ Public | `200 OK` | — |

---

## 🔒 Security Implementation Details

### 1. Trusted Server-Side Verification
Token verification is never performed by blindly decoding JWT payloads locally. Instead, our dependency makes a network call directly to Supabase Auth:
```python
user_response = supabase.auth.get_user(token)
```
If the token has expired, been revoked, or suffered tampering, Supabase rejects the request and our API returns `401 Unauthorized` with `{"error": "Invalid or expired token"}`.

### 2. Reusable Dependency Pattern
Protected endpoints cleanly inject `get_current_user` using FastAPI's dependency injection:
```python
@app.get("/protected/profile")
def protected_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "created_at": current_user["created_at"]
    }
```

---

## 🧪 Live `curl` Execution & Pasted Outputs

### 1. User Signup (`POST /auth/signup`)
```bash
curl.exe -s -i -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "engineer@example.com", "password": "SecurePassword123!"}'
```
**Pasted Output:**
```http
HTTP/1.1 201 Created
date: Wed, 26 Aug 2026 19:04:10 GMT
server: uvicorn
content-length: 138
content-type: application/json

{"id":"8c3cc6ea-d2cc-4427-8a99-4ba5ddb34a97","email":"engineer@example.com","created_at":"2026-08-26 19:04:10.025776+00:00"}
```

### 2. User Login (`POST /auth/login`)
```bash
curl.exe -s -i -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "engineer@example.com", "password": "SecurePassword123!"}'
```
**Pasted Output:**
```http
HTTP/1.1 200 OK
date: Wed, 26 Aug 2026 19:04:11 GMT
server: uvicorn
content-length: 984
content-type: application/json

{
  "access_token": "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "r_12345...",
  "token_type": "bearer",
  "user": {
    "id": "8c3cc6ea-d2cc-4427-8a99-4ba5ddb34a97",
    "email": "engineer@example.com"
  }
}
```

### 3. Public Route (`GET /public/info`)
```bash
curl.exe -s -i http://localhost:8000/public/info
```
**Pasted Output:**
```http
HTTP/1.1 200 OK
date: Wed, 26 Aug 2026 19:04:11 GMT
server: uvicorn
content-length: 50
content-type: application/json

{"message":"Welcome stranger! This info is public."}
```

### 4. Protected Route without Token (401 Error)
```bash
curl.exe -s -i http://localhost:8000/protected/profile
```
**Pasted Output:**
```http
HTTP/1.1 401 Unauthorized
date: Wed, 26 Aug 2026 19:04:12 GMT
server: uvicorn
content-length: 33
content-type: application/json

{"error":"Access token required"}
```

### 5. Protected Route with Valid Bearer Token (200 OK)
```bash
curl.exe -s -i http://localhost:8000/protected/profile \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```
**Pasted Output:**
```http
HTTP/1.1 200 OK
date: Wed, 26 Aug 2026 19:04:13 GMT
server: uvicorn
content-length: 138
content-type: application/json

{"id":"8c3cc6ea-d2cc-4427-8a99-4ba5ddb34a97","email":"engineer@example.com","created_at":"2026-08-26 19:04:10.025776+00:00"}
```

### 6. Protected Route with Tampered Token (401 Error)
```bash
curl.exe -s -i http://localhost:8000/protected/profile \
  -H "Authorization: Bearer TAMPERED_TOKEN_HERE"
```
**Pasted Output:**
```http
HTTP/1.1 401 Unauthorized
date: Wed, 26 Aug 2026 19:04:14 GMT
server: uvicorn
content-length: 37
content-type: application/json

{"error":"Invalid or expired token"}
```

### 7. User Logout (`POST /auth/logout`)
```bash
curl.exe -s -i -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```
**Pasted Output:**
```http
HTTP/1.1 204 No Content
date: Wed, 26 Aug 2026 19:04:15 GMT
server: uvicorn
```

---

## 📖 Swagger UI Interactive Documentation

1. Open `http://localhost:8000/docs` in your web browser.
2. Execute `POST /auth/login` to obtain an `access_token`.
3. Click the green **Authorize** button (with padlock icon) at the top right.
4. Paste the JWT access token in the `Value` field and click **Authorize**.
5. Test `GET /protected/profile` and `GET /protected/dashboard` directly in Swagger UI to view authenticated responses.

```
+-------------------------------------------------------------------------+
|  FlyRank Week 4 Auth API  [1.0.0]                       [ Authorize 🔓 ]|
|                                                                         |
|  POST  /auth/signup       User Signup                                   |
|  POST  /auth/login        User Login                                    |
|  POST  /auth/logout       User Logout                            🔒     |
|  GET   /protected/profile User Profile                           🔒     |
|  GET   /protected/dashboard User Dashboard                      🔒     |
|  GET   /public/info       Public Information                            |
+-------------------------------------------------------------------------+
```

---

## 🧪 Automated Testing

Run the automated pytest test suite:
```bash
pytest tests/test_auth_api.py -v
```
All 9 automated test scenarios (public endpoint, signup validation, login validation, token authorization, tampered token rejection, second route reuse, and logout) execute and pass against Supabase Auth.
