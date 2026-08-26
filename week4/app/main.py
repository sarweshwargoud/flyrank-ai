from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Header, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.auth import supabase
from app.models import AuthRequest

app = FastAPI(
    title="FlyRank Week 4 Auth API",
    description="Authentication and protected routes using Supabase Auth and FastAPI.",
    version="1.0.0"
)


# -------------------------------------------------------------
# Custom Exception Handlers for FlyRank JSON Error Schema
# -------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    error_msg = "Invalid input"
    if errors:
        first_err = errors[0]
        field = first_err.get("loc", ["field"])[-1]
        msg = first_err.get("msg", "field required")
        error_msg = f"{field}: {msg}"
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": error_msg}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


# -------------------------------------------------------------
# Root & Health Endpoints
# -------------------------------------------------------------
@app.get("/", summary="Root Endpoint")
def root():
    return {
        "name": "FlyRank Auth API",
        "version": "1.0.0",
        "status": "online"
    }


@app.get("/health", summary="Health Check")
def health_check():
    return {
        "status": "ok",
        "supabase": "connected" if supabase else "disconnected"
    }


# -------------------------------------------------------------
# Public Endpoint (Stage 2)
# -------------------------------------------------------------
@app.get(
    "/public/info",
    status_code=status.HTTP_200_OK,
    summary="Public Information",
    description="Public endpoint accessible without authentication."
)
def public_info():
    return {
        "message": "Welcome stranger! This info is public."
    }


# -------------------------------------------------------------
# Auth Endpoints (Stage 1)
# -------------------------------------------------------------
@app.post(
    "/auth/signup",
    status_code=status.HTTP_201_CREATED,
    summary="User Signup",
    description="Registers a new user account with Supabase Auth."
)
def signup(body: AuthRequest):
    try:
        response = supabase.auth.sign_up({
            "email": body.email,
            "password": body.password
        })

        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Signup failed with provided details"
            )

        return {
            "id": response.user.id,
            "email": response.user.email,
            "created_at": str(response.user.created_at) if response.user.created_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post(
    "/auth/login",
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticates user credentials and returns JWT access and refresh tokens."
)
def login(body: AuthRequest):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": body.email,
            "password": body.password
        })

        if not response.session or not response.session.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid login credentials"
            )

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "token_type": "bearer",
            "user": {
                "id": response.user.id if response.user else None,
                "email": response.user.email if response.user else None
            }
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login credentials"
        )


# -------------------------------------------------------------
# Protected Route Placeholder (Stage 2: unverified header check)
# -------------------------------------------------------------
@app.get(
    "/protected/profile",
    status_code=status.HTTP_200_OK,
    summary="User Profile (Unverified Guard)",
    description="Protected endpoint checking token presence in Authorization header."
)
def protected_profile_unverified(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.strip().startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token required"
        )

    parts = authorization.strip().split(" ", 1)
    if len(parts) != 2 or not parts[1].strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token required"
        )

    return {
        "message": "Token present (unverified profile placeholder)"
    }
