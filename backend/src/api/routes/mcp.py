import base64
import binascii
import json
from hashlib import sha256
from time import perf_counter
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, HTTPException
import httpx
from pydantic import BaseModel

from src.auth.security import Principal, enforce_user_scope, get_current_principal
from src.db.models import UserProfile
from src.db.repositories import (
    get_default_voice_persona_id,
    list_public_thread_memories,
    list_thread_memories,
    upsert_profile_fields,
    write_audit_log,
    write_thread_memory,
    write_tool_event,
)
from src.db.session import SessionLocal
from src.mcp.contracts import MCP_RESOURCES, MCP_TOOLS
from src.services.search_provider import get_search_provider
from src.services.tts_provider import get_tts_provider
from src.services.voice_provider import get_voice_provider

router = APIRouter()


class MCPInvokeRequest(BaseModel):
    tool_name: str
    actor: str
    role: str = "user"
    payload: dict


class MCPResourceReadRequest(BaseModel):
    uri: str
    actor: str


class MCPResourceWriteRequest(BaseModel):
    uri: str
    actor: str
    data: dict


def mcp_error(
    *,
    status_code: int,
    error_code: str,
    message: str,
    retryable: bool,
    fallback_path: str | None = None,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "error_code": error_code,
            "message": message,
            "retryable": retryable,
            "fallback_path": fallback_path,
        },
    )


@router.get("/resources")
def list_resources(principal: Principal = Depends(get_current_principal)) -> dict:
    _ = principal
    return {"resources": MCP_RESOURCES}


@router.get("/tools")
def list_tools(principal: Principal = Depends(get_current_principal)) -> dict:
    _ = principal
    return {"tools": MCP_TOOLS}


@router.post("/invoke")
async def invoke_tool(req: MCPInvokeRequest, principal: Principal = Depends(get_current_principal)) -> dict:
    start = perf_counter()
    request_id = req.payload.get("request_id")
    payload_hash = sha256(json.dumps(req.payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:32]
    tool_names = {tool["name"] for tool in MCP_TOOLS}
    if req.tool_name not in tool_names:
        with SessionLocal() as db:
            write_tool_event(
                db,
                request_id=request_id,
                tool_name=req.tool_name,
                status="not_found",
                latency_ms=int((perf_counter() - start) * 1000),
                payload_hash=payload_hash,
            )
            db.commit()
        raise mcp_error(
            status_code=404,
            error_code="TOOL_NOT_FOUND",
            message="Tool not registered",
            retryable=False,
            fallback_path=None,
        )

    if principal.role != "admin" and req.actor != principal.user_id:
        with SessionLocal() as db:
            write_audit_log(
                db,
                request_id=request_id,
                actor_user_id=principal.user_id,
                action=f"mcp.invoke:{req.tool_name}",
                resource=req.payload.get("resource"),
                decision="deny",
                reason="actor_scope_mismatch",
            )
            write_tool_event(
                db,
                request_id=request_id,
                tool_name=req.tool_name,
                status="denied",
                latency_ms=int((perf_counter() - start) * 1000),
                payload_hash=payload_hash,
            )
            db.commit()
        raise mcp_error(
            status_code=403,
            error_code="ACCESS_DENIED",
            message="Actor scope mismatch",
            retryable=False,
            fallback_path="use authenticated actor user_id",
        )

    response_payload: dict
    if req.tool_name == "tool.memory.upsert_profile":
        target_user_id = req.payload.get("user_id", req.actor)
        enforce_user_scope(principal, target_user_id)
        fields = req.payload.get("fields", {})
        with SessionLocal() as db:
            version = upsert_profile_fields(db, target_user_id, fields)
            write_audit_log(
                db,
                request_id=request_id,
                actor_user_id=principal.user_id,
                action="mcp.invoke:tool.memory.upsert_profile",
                resource=f"memory://user/{target_user_id}/profile",
                decision="allow",
                reason=None,
            )
            write_tool_event(
                db,
                request_id=request_id,
                tool_name=req.tool_name,
                status="success",
                latency_ms=int((perf_counter() - start) * 1000),
                payload_hash=payload_hash,
            )
            db.commit()
        response_payload = {"status": "ok", "decision": "allowed", "profile_version": version}
    elif req.tool_name == "tool.search_web":
        query = str(req.payload.get("query", "")).strip()
        if not query:
            raise mcp_error(
                status_code=400,
                error_code="INVALID_INPUT",
                message="query is required for tool.search_web",
                retryable=False,
                fallback_path="send non-empty query",
            )
        recency_days = int(req.payload.get("recency_days", 7))
        try:
            result = get_search_provider().search(query=query, recency_days=recency_days)
        except Exception:
            raise mcp_error(
                status_code=503,
                error_code="UPSTREAM_UNAVAILABLE",
                message="Web search provider is temporarily unavailable",
                retryable=True,
                fallback_path="proceed without web context",
            )
        with SessionLocal() as db:
            write_audit_log(
                db,
                request_id=request_id,
                actor_user_id=principal.user_id,
                action="mcp.invoke:tool.search_web",
                resource="external://search",
                decision="allow",
                reason=f"provider:{result.provider}",
            )
            write_tool_event(
                db,
                request_id=request_id,
                tool_name=req.tool_name,
                status="success",
                latency_ms=int((perf_counter() - start) * 1000),
                payload_hash=payload_hash,
            )
            db.commit()
        response_payload = {
            "status": "ok",
            "decision": "allowed",
            "result": {
                "citations": result.citations,
                "confidence": result.confidence,
                "provider": result.provider,
            },
        }
    elif req.tool_name == "tool.voice.transcribe":
        audio_base64 = req.payload.get("audio_base64")
        user_id = req.payload.get("user_id", req.actor)
        enforce_user_scope(principal, str(user_id))
        if not audio_base64:
            raise mcp_error(
                status_code=400,
                error_code="INVALID_INPUT",
                message="audio_base64 is required for tool.voice.transcribe",
                retryable=False,
                fallback_path="provide base64-encoded audio bytes",
            )
        try:
            audio_bytes = base64.b64decode(audio_base64)
        except (binascii.Error, ValueError):
            raise mcp_error(
                status_code=400,
                error_code="INVALID_INPUT",
                message="audio_base64 is not valid base64",
                retryable=False,
                fallback_path="re-encode audio bytes to base64",
            )
        provider = get_voice_provider()
        mime_type = str(req.payload.get("mime_type", "audio/webm"))
        try:
            result = await provider.transcribe(audio_bytes, str(req.payload.get("language", "en")), mime_type)
        except httpx.HTTPStatusError as exc:
            raise mcp_error(
                status_code=503,
                error_code="UPSTREAM_UNAVAILABLE",
                message=f"Voice provider failed: {exc.response.status_code}",
                retryable=True,
                fallback_path="retry with a different recording format or provider",
            )
        except Exception:
            raise mcp_error(
                status_code=503,
                error_code="UPSTREAM_UNAVAILABLE",
                message="Voice transcription is temporarily unavailable",
                retryable=True,
                fallback_path="use text input mode",
            )
        with SessionLocal() as db:
            write_audit_log(
                db,
                request_id=request_id,
                actor_user_id=principal.user_id,
                action="mcp.invoke:tool.voice.transcribe",
                resource=f"voice://user/{user_id}/audio",
                decision="allow",
                reason="provider_invoked",
            )
            write_tool_event(
                db,
                request_id=request_id,
                tool_name=req.tool_name,
                status="success",
                latency_ms=int((perf_counter() - start) * 1000),
                payload_hash=payload_hash,
            )
            db.commit()
        response_payload = {
            "status": "ok",
            "decision": "allowed",
            "result": {
                "transcript": result.transcript,
                "segments": [segment.model_dump() for segment in result.segments],
                "confidence": result.confidence,
                "provider": result.provider,
            },
        }
    elif req.tool_name == "tool.voice.speak":
        text = str(req.payload.get("text", "")).strip()
        user_id = req.payload.get("user_id", req.actor)
        enforce_user_scope(principal, str(user_id))
        if not text:
            raise mcp_error(
                status_code=400,
                error_code="INVALID_INPUT",
                message="text is required for tool.voice.speak",
                retryable=False,
                fallback_path="provide non-empty text",
            )
        persona_id = req.payload.get("persona_id")
        if persona_id is None:
            with SessionLocal() as db:
                persona_id = get_default_voice_persona_id(db, str(user_id))
        tts = get_tts_provider()
        output = tts.synthesize(text=text, persona_id=str(persona_id) if persona_id is not None else None)
        with SessionLocal() as db:
            write_audit_log(
                db,
                request_id=request_id,
                actor_user_id=principal.user_id,
                action="mcp.invoke:tool.voice.speak",
                resource=f"voice://user/{user_id}/tts",
                decision="allow",
                reason=f"provider:{output.provider}",
            )
            write_tool_event(
                db,
                request_id=request_id,
                tool_name=req.tool_name,
                status="success",
                latency_ms=int((perf_counter() - start) * 1000),
                payload_hash=payload_hash,
            )
            db.commit()
        response_payload = {
            "status": "ok",
            "decision": "allowed",
            "result": {
                "audio_base64": output.audio_base64,
                "mime_type": output.mime_type,
                "provider": output.provider,
            },
        }
    else:
        with SessionLocal() as db:
            write_audit_log(
                db,
                request_id=request_id,
                actor_user_id=principal.user_id,
                action=f"mcp.invoke:{req.tool_name}",
                resource=req.payload.get("resource"),
                decision="deny",
                reason="tool_not_implemented",
            )
            write_tool_event(
                db,
                request_id=request_id,
                tool_name=req.tool_name,
                status="not_implemented",
                latency_ms=int((perf_counter() - start) * 1000),
                payload_hash=payload_hash,
            )
            db.commit()
        raise mcp_error(
            status_code=501,
            error_code="TOOL_NOT_IMPLEMENTED",
            message="Tool is registered but not implemented",
            retryable=False,
            fallback_path=None,
        )

    return response_payload


@router.post("/resource/read")
def read_resource(req: MCPResourceReadRequest, principal: Principal = Depends(get_current_principal)) -> dict:
    if principal.role != "admin" and req.actor != principal.user_id:
        raise mcp_error(
            status_code=403,
            error_code="ACCESS_DENIED",
            message="Actor scope mismatch",
            retryable=False,
            fallback_path="use authenticated actor user_id",
        )

    if req.uri.startswith("memory://user/") and req.uri.endswith("/profile"):
        parts = req.uri.split("/")
        user_id = parts[3] if len(parts) > 3 else ""
        enforce_user_scope(principal, user_id)
        with SessionLocal() as db:
            profile = db.get(UserProfile, user_id)
        if profile is None:
            return {"status": "ok", "uri": req.uri, "data": None}
        return {
            "status": "ok",
            "uri": req.uri,
            "data": {
                "preferred_tone": profile.preferred_tone,
                "organization": profile.organization,
                "signature": profile.signature,
                "prefs_json": profile.prefs_json,
                "version": profile.version,
            },
        }

    if req.uri.startswith("memory://user/") and "/threads" in req.uri:
        uri_without_query, _, query = req.uri.partition("?")
        parts = uri_without_query.split("/")
        user_id = parts[3] if len(parts) > 3 else ""
        enforce_user_scope(principal, user_id)
        params = parse_qs(query)
        limit = 20
        if "limit" in params and params["limit"]:
            try:
                limit = int(params["limit"][0])
            except ValueError:
                limit = 20
        include_public = True
        if "include_public" in params and params["include_public"]:
            include_public = str(params["include_public"][0]).lower() not in {"0", "false", "no"}
        with SessionLocal() as db:
            threads = list_thread_memories(db, user_id, limit=limit)
            if principal.role != "admin" and include_public:
                public_threads = list_public_thread_memories(db, limit=limit)
                own_ids = {item["thread_id"] for item in threads}
                for item in public_threads:
                    if item["thread_id"] not in own_ids:
                        threads.append(item)
                threads = sorted(threads, key=lambda x: x.get("created_at", ""), reverse=True)[: max(1, min(limit, 100))]
        return {"status": "ok", "uri": req.uri, "data": {"threads": threads}}

    if req.uri.startswith("templates://email/"):
        template_id = req.uri.split("/")[-1]
        templates = {
            "follow_up": "Dear {recipient},\n\nFollowing up on {topic}. Please confirm next steps.\n\nBest regards,",
            "apology": "Hello {recipient},\n\nI apologize for {issue}. Thank you for your patience.\n\nSincerely,",
            "informational": "Dear {recipient},\n\nSharing an update regarding {topic}.\n\nRegards,",
        }
        return {"status": "ok", "uri": req.uri, "data": {"template": templates.get(template_id, "")}}

    if req.uri == "policy://safety/ruleset":
        return {
            "status": "ok",
            "uri": req.uri,
            "data": {
                "block_patterns": ["ignore previous instructions", "reveal system prompt", "exfiltrate"],
                "dlp_forbidden_tags": ["PII"],
            },
        }

    raise mcp_error(
        status_code=404,
        error_code="RESOURCE_NOT_FOUND",
        message="Resource not found",
        retryable=False,
        fallback_path=None,
    )


@router.post("/resource/write")
def write_resource(req: MCPResourceWriteRequest, principal: Principal = Depends(get_current_principal)) -> dict:
    if principal.role != "admin" and req.actor != principal.user_id:
        raise mcp_error(
            status_code=403,
            error_code="ACCESS_DENIED",
            message="Actor scope mismatch",
            retryable=False,
            fallback_path="use authenticated actor user_id",
        )

    if req.uri.startswith("memory://user/") and req.uri.endswith("/profile"):
        parts = req.uri.split("/")
        user_id = parts[3] if len(parts) > 3 else ""
        enforce_user_scope(principal, user_id)
        with SessionLocal() as db:
            version = upsert_profile_fields(db, user_id, req.data)
            db.commit()
        return {"status": "ok", "uri": req.uri, "version": version}

    if req.uri.startswith("memory://user/") and req.uri.endswith("/threads"):
        parts = req.uri.split("/")
        user_id = parts[3] if len(parts) > 3 else ""
        enforce_user_scope(principal, user_id)
        with SessionLocal() as db:
            thread_id = write_thread_memory(db, user_id, req.data)
            db.commit()
        return {"status": "ok", "uri": req.uri, "thread_id": thread_id}

    raise mcp_error(
        status_code=403,
        error_code="RESOURCE_READ_ONLY",
        message="Only memory profile and memory threads resources are writable",
        retryable=False,
        fallback_path="write to memory://user/{user_id}/profile or memory://user/{user_id}/threads",
    )
