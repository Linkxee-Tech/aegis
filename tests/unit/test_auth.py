import asyncio

import pytest
from fastapi import HTTPException
from starlette.datastructures import Headers, QueryParams

from backend.services import auth


class FakeHttpRequest:
    def __init__(self, headers: dict[str, str] | None = None, query_params: dict[str, str] | None = None) -> None:
        self.headers = Headers(headers or {})
        self.query_params = QueryParams(query_params or {})


class FakeWebSocket:
    def __init__(self, headers: dict[str, str] | None = None, query_params: dict[str, str] | None = None) -> None:
        self.headers = Headers(headers or {})
        self.query_params = QueryParams(query_params or {})


@pytest.fixture(autouse=True)
def reset_auth_settings():
    original = {
        "auth_enabled": auth.settings.auth_enabled,
        "viewer_api_keys": auth.settings.viewer_api_keys,
        "operator_api_keys": auth.settings.operator_api_keys,
        "admin_api_keys": auth.settings.admin_api_keys,
    }
    yield
    for key, value in original.items():
        setattr(auth.settings, key, value)


def test_auth_disabled_allows_anonymous_demo_access():
    auth.settings.auth_enabled = False

    context = auth.get_auth_context(FakeHttpRequest())

    assert context.authenticated is False
    assert context.role == "admin"


def test_bearer_token_maps_to_viewer_role():
    auth.settings.auth_enabled = True
    auth.settings.viewer_api_keys = "viewer-token"

    context = auth.get_auth_context(FakeHttpRequest(headers={"authorization": "Bearer viewer-token"}))

    assert context.authenticated is True
    assert context.role == "viewer"


def test_query_token_works_for_websocket_connections():
    auth.settings.auth_enabled = True
    auth.settings.operator_api_keys = "operator-token"

    context = auth.get_websocket_auth_context(FakeWebSocket(query_params={"token": "operator-token"}))

    assert context.authenticated is True
    assert context.role == "operator"


def test_unknown_token_is_rejected():
    auth.settings.auth_enabled = True
    auth.settings.viewer_api_keys = "viewer-token"

    with pytest.raises(HTTPException) as exc_info:
        auth.get_auth_context(FakeHttpRequest(headers={"x-api-key": "bad-token"}))

    assert getattr(exc_info.value, "status_code", None) == 403


def test_role_dependency_blocks_viewer_from_operator_endpoint():
    auth.settings.auth_enabled = True
    auth.settings.viewer_api_keys = "viewer-token"

    dependency = auth.require_roles("operator", "admin")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(dependency(FakeHttpRequest(headers={"authorization": "Bearer viewer-token"})))

    assert getattr(exc_info.value, "status_code", None) == 403
