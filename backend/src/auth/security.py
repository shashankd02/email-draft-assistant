from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from src.core.config import settings


@dataclass
class Principal:
    user_id: str
    role: str


bearer_scheme = HTTPBearer(auto_error=True)


def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.now(tz=timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": user_id, "role": role, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def get_current_principal(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> Principal:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        role = payload.get("role", "user")
        if not user_id:
            raise HTTPException(status_code=401, detail={"error_code": "UNAUTHORIZED", "message": "Invalid token payload"})
        return Principal(user_id=user_id, role=role)
    except JWTError as exc:
        raise HTTPException(status_code=401, detail={"error_code": "UNAUTHORIZED", "message": "Token validation failed"}) from exc


def enforce_user_scope(principal: Principal, target_user_id: str) -> None:
    if principal.role != "admin" and principal.user_id != target_user_id:
        raise HTTPException(status_code=403, detail={"error_code": "ACCESS_DENIED", "message": "Scope violation"})


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 240000)
    return f"pbkdf2_sha256${salt}${derived.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        scheme, salt, digest = password_hash.split("$", 2)
    except ValueError:
        return False
    if scheme != "pbkdf2_sha256":
        return False
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 240000).hex()
    return hmac.compare_digest(derived, digest)
