from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.auth.security import Principal, create_access_token, get_current_principal, hash_password, verify_password
from src.core.config import settings
from src.db.models import User
from src.db.repositories import delete_user_data, delete_user_transcripts, write_audit_log
from src.db.session import SessionLocal
from src.services.memory_vector import get_vector_memory_service

router = APIRouter()


class AuthTokenRequest(BaseModel):
    user_id: str
    role: str = "user"
    bootstrap_secret: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


@router.post("/token", response_model=AuthTokenResponse)
def issue_token(payload: AuthTokenRequest) -> AuthTokenResponse:
    if settings.app_env.lower() != "development":
        raise HTTPException(
            status_code=403,
            detail={"error_code": "ACCESS_DENIED", "message": "Bootstrap token endpoint is disabled outside development"},
        )
    if payload.bootstrap_secret != settings.auth_bootstrap_secret:
        raise HTTPException(status_code=403, detail={"error_code": "ACCESS_DENIED", "message": "Invalid bootstrap secret"})

    token = create_access_token(payload.user_id, payload.role)
    with SessionLocal() as db:
        write_audit_log(
            db,
            request_id=None,
            actor_user_id=payload.user_id,
            action="auth.token.issue",
            resource="auth://token",
            decision="allow",
            reason=f"role:{payload.role}",
        )
        db.commit()
    return AuthTokenResponse(access_token=token, expires_in_minutes=settings.jwt_expire_minutes)


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "user"
    email: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/register", response_model=AuthTokenResponse)
def register(payload: RegisterRequest) -> AuthTokenResponse:
    username = payload.username.strip()
    if len(username) < 3:
        raise HTTPException(status_code=400, detail={"error_code": "INVALID_INPUT", "message": "Username must be at least 3 characters"})
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail={"error_code": "INVALID_INPUT", "message": "Password must be at least 8 characters"})
    requested_role = (payload.role or "user").strip().lower()
    if requested_role == "admin" and settings.app_env.lower() != "development":
        raise HTTPException(
            status_code=403,
            detail={"error_code": "ACCESS_DENIED", "message": "Admin self-registration is disabled outside development"},
        )
    role = requested_role if requested_role in {"user", "admin"} else "user"
    email = (payload.email or "").strip() or (username if "@" in username else f"{username}@local.dev")

    with SessionLocal() as db:
        existing = db.get(User, username)
        if existing is not None:
            raise HTTPException(status_code=409, detail={"error_code": "CONFLICT", "message": "Username already exists"})
        email_exists = db.query(User).filter(User.email == email).first()
        if email_exists is not None:
            raise HTTPException(status_code=409, detail={"error_code": "CONFLICT", "message": "Email already exists"})

        db.add(
            User(
                id=username,
                email=email,
                password_hash=hash_password(payload.password),
                role=role,
            )
        )
        write_audit_log(
            db,
            request_id=None,
            actor_user_id=username,
            action="auth.register",
            resource="auth://register",
            decision="allow",
            reason=f"role:{role}",
        )
        db.commit()

    token = create_access_token(username, role)
    return AuthTokenResponse(access_token=token, expires_in_minutes=settings.jwt_expire_minutes)


@router.post("/login", response_model=AuthTokenResponse)
def login(payload: LoginRequest) -> AuthTokenResponse:
    username = payload.username.strip()
    with SessionLocal() as db:
        user = db.get(User, username)
        if user is None or not user.password_hash or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail={"error_code": "UNAUTHORIZED", "message": "Invalid username or password"})
        write_audit_log(
            db,
            request_id=None,
            actor_user_id=username,
            action="auth.login",
            resource="auth://login",
            decision="allow",
            reason=f"role:{user.role}",
        )
        db.commit()
        role = user.role

    token = create_access_token(username, role)
    return AuthTokenResponse(access_token=token, expires_in_minutes=settings.jwt_expire_minutes)


@router.delete("/me/transcripts")
def delete_my_transcripts(principal: Principal = Depends(get_current_principal)) -> dict:
    with SessionLocal() as db:
        deleted_count = delete_user_transcripts(db, principal.user_id)
        write_audit_log(
            db,
            request_id=None,
            actor_user_id=principal.user_id,
            action="voice.transcripts.delete",
            resource=f"voice://user/{principal.user_id}/transcripts",
            decision="allow",
            reason=f"deleted:{deleted_count}",
        )
        db.commit()
    return {"status": "ok", "deleted_transcripts": deleted_count}


@router.delete("/me")
def delete_my_account(principal: Principal = Depends(get_current_principal)) -> dict:
    with SessionLocal() as db:
        deleted = delete_user_data(db, principal.user_id)
        write_audit_log(
            db,
            request_id=None,
            actor_user_id=principal.user_id,
            action="auth.account.delete",
            resource=f"user://{principal.user_id}",
            decision="allow",
            reason="self_delete",
        )
        db.commit()
    get_vector_memory_service().delete_user_memory(principal.user_id)
    return {"status": "ok", "deleted": deleted}
