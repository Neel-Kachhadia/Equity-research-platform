"""
Authentication module — JWT-based register / login for EREBUS.
Tables created on startup if not present.
"""

import bcrypt
import jwt
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator

from core.config import settings
from core.database import get_cursor, execute_single, execute_write

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])

# ── Config ────────────────────────────────────────────────────────────────────
JWT_ALGORITHM  = "HS256"
ACCESS_TTL_H   = 72   # hours before token expires


# ── Pydantic schemas ──────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    name:     str
    email:    EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("name")
    @classmethod
    def nonempty_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name is required")
        return v


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class AuthResponse(BaseModel):
    token:      str
    user_id:    int
    name:       str
    email:      str


# ── Helpers ───────────────────────────────────────────────────────────────────
def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _create_token(user_id: int, email: str) -> str:
    payload = {
        "sub":   str(user_id),
        "email": email,
        "iat":   datetime.now(timezone.utc),
        "exp":   datetime.now(timezone.utc) + timedelta(hours=ACCESS_TTL_H),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=JWT_ALGORITHM)


def ensure_users_table() -> None:
    """Idempotent — create users table if it doesn't exist. Called from main.py lifespan."""
    with get_cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            SERIAL PRIMARY KEY,
                name          VARCHAR(120) NOT NULL,
                email         VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                role          VARCHAR(30)  NOT NULL DEFAULT 'analyst',
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS users_email_idx ON users(email)
        """)
    logger.info("users table ready")


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest):
    # Duplicate check
    existing = execute_single(
        "SELECT id FROM users WHERE email = %s", (body.email.lower(),)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    hashed = _hash_password(body.password)
    user_id = execute_write(
        "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
        (body.name.strip(), body.email.lower(), hashed),
        returning="id",
    )
    if not user_id:
        raise HTTPException(status_code=500, detail="Failed to create account")

    token = _create_token(user_id, body.email.lower())
    logger.info(f"New user registered: {body.email}")
    return AuthResponse(token=token, user_id=user_id, name=body.name.strip(), email=body.email.lower())


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest):
    user = execute_single(
        "SELECT id, name, email, password_hash FROM users WHERE email = %s",
        (body.email.lower(),),
    )
    if not user or not _verify_password(body.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = _create_token(user["id"], user["email"])
    logger.info(f"User logged in: {user['email']}")
    return AuthResponse(token=token, user_id=user["id"], name=user["name"], email=user["email"])


@router.get("/me")
def me_stub():
    """Placeholder — token verification to be added as FastAPI dependency."""
    return {"detail": "Attach Authorization: Bearer <token> to verify"}
