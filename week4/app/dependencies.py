from typing import Optional, Dict, Any
from fastapi import Header, HTTPException, status
from app.auth import supabase


def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Reusable FastAPI authentication dependency.
    Extracts the Bearer token from the Authorization header,
    verifies it against Supabase Auth, and returns the authenticated user data.
    """
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

    token = parts[1].strip()

    try:
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

        user = user_response.user
        return {
            "id": user.id,
            "email": user.email,
            "created_at": str(user.created_at) if user.created_at else None,
            "token": token
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
