"""
ScamShield AI — Authentication & Account Lifecycle Endpoints (Items 1, 2, 3, 10, 18)

Provides REST endpoints for:
- User registration and email verification (Items 1 & 3)
- Authentication & login / logout (Item 1)
- Password reset flow (Item 2)
- Row-Level Security user history (Item 10)
- Account deletion & data purging (Item 18)
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status

from app.services.auth_service import (
    auth_service,
    generate_session_token,
    verify_session_token,
)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


# -----------------------------------------------------------------------------
# Pydantic Schemas for Auth Payloads
# -----------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    email: str = Field(..., pattern=EMAIL_REGEX, max_length=255)
    password: str = Field(..., min_length=8, description="Minimum 8 characters")


class LoginRequest(BaseModel):
    email: str = Field(..., pattern=EMAIL_REGEX, max_length=255)
    password: str


class VerifyEmailRequest(BaseModel):
    email: str = Field(..., pattern=EMAIL_REGEX, max_length=255)
    code: str = Field(..., min_length=6, max_length=6)


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., pattern=EMAIL_REGEX, max_length=255)



class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


# -----------------------------------------------------------------------------
# Dependency: Extract Authenticated User
# -----------------------------------------------------------------------------

async def get_current_user_optional(request: Request) -> Optional[Dict[str, Any]]:
    """Extracts user from Authorization header or session cookie if present."""
    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    elif "scamshield_token" in request.cookies:
        token = request.cookies.get("scamshield_token")

    if not token:
        return None

    payload = verify_session_token(token)
    if not payload:
        return None

    user = auth_service.get_user_by_id(payload.get("sub"))
    return user


async def get_current_user_required(
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    """Requires an authenticated user or raises HTTP 401 Unauthorized."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# -----------------------------------------------------------------------------
# Auth Routes
# -----------------------------------------------------------------------------

@router.post("/register", status_code=status.HTTP_201_CREATED, summary="Register New User Account")
async def register(payload: RegisterRequest, response: Response):
    """Registers user and issues verification OTP code (Item 1 & 3)."""
    try:
        data = auth_service.register_user(payload.email, payload.password)
        # Set HttpOnly session cookie
        response.set_cookie(
            key="scamshield_token",
            value=data["token"],
            httponly=True,
            samesite="lax",
            max_age=86400,
        )
        return {
            "status": "success",
            "message": "Account created successfully.",
            "user_id": data["user_id"],
            "email": data["email"],
            "is_verified": data["is_verified"],
            "verification_code": data["verification_code"],  # Returned for demo/simulated verification
            "token": data["token"],
        }
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.post("/verify-email", summary="Verify User Email (Item 3)")
async def verify_email(payload: VerifyEmailRequest):
    """Validates 6-digit verification code to confirm user email address."""
    success = auth_service.verify_email(payload.email, payload.code)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code.",
        )
    return {"status": "success", "message": "Email verified successfully."}


@router.post("/login", summary="User Login & Session Token (Item 1)")
async def login(payload: LoginRequest, response: Response):
    """Authenticates user credentials and issues session token."""
    user = auth_service.authenticate_user(payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    response.set_cookie(
        key="scamshield_token",
        value=user["token"],
        httponly=True,
        samesite="lax",
        max_age=86400,
    )
    return {
        "status": "success",
        "message": "Login successful.",
        "user_id": user["user_id"],
        "email": user["email"],
        "is_verified": user["is_verified"],
        "token": user["token"],
    }


@router.post("/logout", summary="User Logout")
async def logout(response: Response):
    """Clears session cookie."""
    response.delete_cookie(key="scamshield_token")
    return {"status": "success", "message": "Logged out successfully."}


@router.get("/me", summary="Get Authenticated User Profile")
async def get_me(user: Dict[str, Any] = Depends(get_current_user_required)):
    """Returns profile for currently authenticated user."""
    return {"status": "success", "user": user}


@router.post("/forgot-password", summary="Request Password Reset")
async def forgot_password(payload: ForgotPasswordRequest):
    """
    Initiates password reset workflow.
    Always returns a generic, uniform message to prevent account enumeration.
    Never exposes reset tokens in public HTTP responses, headers, or application logs.
    """
    auth_service.create_password_reset(payload.email)
    return {
        "status": "success",
        "message": "If an account exists with this email address, password reset instructions have been dispatched.",
    }


@router.post("/reset-password", summary="Reset Password with Token (Item 2)")
async def reset_password(payload: ResetPasswordRequest):
    """Sets new password using reset token."""
    try:
        success = auth_service.reset_password(payload.token, payload.new_password)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token.",
            )
        return {"status": "success", "message": "Password has been successfully updated."}
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.get("/history", summary="User Scan History with Row-Level Isolation (Item 10)")
async def get_user_scan_history(user: Dict[str, Any] = Depends(get_current_user_required)):
    """Returns private scan records belonging strictly to the authenticated user."""
    scans = auth_service.get_user_scans(user["id"])
    return {"status": "success", "scans": scans}


@router.delete("/account", summary="Delete Account & Purge Data (Item 18)")
async def delete_account(
    response: Response,
    user: Dict[str, Any] = Depends(get_current_user_required),
):
    """
    GDPR Right to Erasure (Article 17):
    Permanently deletes user account and cascades deletion of all scan history.
    """
    auth_service.delete_account(user["id"])
    response.delete_cookie(key="scamshield_token")
    return {
        "status": "success",
        "message": "Account and all associated scan history have been permanently purged.",
    }
