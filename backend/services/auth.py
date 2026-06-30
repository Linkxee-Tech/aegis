"""
Gateway authentication and role-based authorization helpers.

The security model is intentionally lightweight for this build: API keys are
provided via environment variables, and each key maps to a role. This keeps the
local demo flow simple while still letting the gateway enforce viewer/operator
boundaries in deployed environments.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from fastapi import Header, HTTPException, Query, WebSocket, status

from backend.config.settings import get_settings

settings = get_settings()

ROLE_HIERARCHY = {
    "viewer": 0,
    "operator": 1,
    "admin": 2,
}


@dataclass(frozen=True)
class AuthContext:
    authenticated: bool
    role: str
    token_source: str | None = None


def _normalize_token(token: str | None) -> str | None:
    if token is None:
        return None
    cleaned = token.strip()
    return cleaned or None


def _extract_bearer_token(authorization: str | None) -> str | None:
    auth_header = _normalize_token(authorization)
    if auth_header and auth_header.lower().startswith("bearer "):
        return _normalize_token(auth_header[7:])
    return None


def _extract_api_key(
    x_api_key: str | None,
    x_aegis_api_key: str | None,
    token: str | None,
) -> str | None:
    return _normalize_token(
        x_api_key
        or x_aegis_api_key
        or token
    )


def _extract_websocket_token(websocket: WebSocket) -> str | None:
    auth_header = _normalize_token(websocket.headers.get("authorization"))
    if auth_header and auth_header.lower().startswith("bearer "):
        return _normalize_token(auth_header[7:])
    return _normalize_token(
        websocket.headers.get("x-api-key")
        or websocket.headers.get("x-aegis-api-key")
        or websocket.query_params.get("token")
    )


def _role_for_token(token: str) -> str | None:
    if token in settings.parsed_api_keys(settings.admin_api_keys):
        return "admin"
    if token in settings.parsed_api_keys(settings.operator_api_keys):
        return "operator"
    if token in settings.parsed_api_keys(settings.viewer_api_keys):
        return "viewer"
    return None


def get_auth_context(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    x_aegis_api_key: str | None = Header(default=None, alias="X-Aegis-API-Key"),
    token: str | None = Query(default=None),
) -> AuthContext:
    """
    Resolve the current caller's role.

    When auth is disabled, every request is treated as an authenticated admin so
    the local demo remains frictionless. When auth is enabled, a valid key is
    required.
    """
    if not settings.auth_enabled:
        return AuthContext(authenticated=False, role="admin", token_source=None)

    bearer_token = _extract_bearer_token(authorization)
    api_key = _extract_api_key(x_api_key, x_aegis_api_key, token)
    resolved_token = bearer_token or api_key
    if resolved_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide a Bearer token or X-API-Key header.",
        )

    role = _role_for_token(resolved_token)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your API key is not authorized for this gateway.",
        )

    token_source = "query" if token else "header"
    return AuthContext(authenticated=True, role=role, token_source=token_source)


def get_websocket_auth_context(websocket: WebSocket) -> AuthContext:
    if not settings.auth_enabled:
        return AuthContext(authenticated=False, role="admin", token_source=None)

    token = _extract_websocket_token(websocket)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide a Bearer token, X-API-Key header, or ?token=",
        )

    role = _role_for_token(token)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your API key is not authorized for this gateway.",
        )

    token_source = "query" if websocket.query_params.get("token") else "header"
    return AuthContext(authenticated=True, role=role, token_source=token_source)


def require_roles(*allowed_roles: str):
    allowed = tuple(allowed_roles)

    async def dependency(
        authorization: str | None = Header(default=None),
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
        x_aegis_api_key: str | None = Header(default=None, alias="X-Aegis-API-Key"),
        token: str | None = Query(default=None),
    ) -> AuthContext:
        context = get_auth_context(
            authorization=authorization,
            x_api_key=x_api_key,
            x_aegis_api_key=x_aegis_api_key,
            token=token,
        )
        if not settings.auth_enabled:
            return context

        if context.role == "admin" or context.role in allowed:
            return context

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{context.role}' cannot access this endpoint. Allowed roles: {', '.join(allowed)}.",
        )

    return dependency


def highest_role(tokens: Iterable[str]) -> str | None:
    roles = [role for token in tokens if (role := _role_for_token(token))]
    if not roles:
        return None
    return max(roles, key=lambda role: ROLE_HIERARCHY[role])
