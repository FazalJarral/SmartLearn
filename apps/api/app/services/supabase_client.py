from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from app.core.config import Settings
from app.core.errors import ApiError


@dataclass(frozen=True)
class Actor:
    actor_type: str
    user_id: str | None = None
    guest_session_id: str | None = None


@dataclass(frozen=True)
class GuestSession:
    id: str
    token: str
    expires_at: datetime


class SupabaseService:
    def __init__(self, settings: Settings):
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise ApiError("supabase_not_configured", "Supabase is not configured on the server.", 500)
        self.settings = settings
        self.rest_url = f"{settings.supabase_url.rstrip('/')}/rest/v1"
        self.auth_url = f"{settings.supabase_url.rstrip('/')}/auth/v1"
        self.storage_url = f"{settings.supabase_url.rstrip('/')}/storage/v1"

    @property
    def service_headers(self) -> dict[str, str]:
        return {
            "apikey": self.settings.supabase_service_role_key,
            "authorization": f"Bearer {self.settings.supabase_service_role_key}",
            "content-type": "application/json",
        }

    def _hash_secret(self, value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    async def verify_bearer(self, authorization: str | None) -> Actor | None:
        if not authorization or not authorization.lower().startswith("bearer "):
            return None
        token = authorization.split(" ", 1)[1].strip()
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.auth_url}/user",
                headers={
                    "apikey": self.settings.supabase_anon_key,
                    "authorization": f"Bearer {token}",
                },
            )
        if response.status_code == 401:
            raise ApiError("invalid_session", "Sign in again to continue.", 401)
        response.raise_for_status()
        return Actor(actor_type="registered", user_id=response.json()["id"])

    async def create_guest_session(self, abuse_fingerprint_hash: str | None = None) -> GuestSession:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(hours=24)
        payload = {
            "token_hash": self._hash_secret(token),
            "expires_at": expires_at.isoformat(),
            "abuse_fingerprint_hash": abuse_fingerprint_hash,
        }
        rows = await self.insert("guest_sessions", payload)
        return GuestSession(id=rows[0]["id"], token=token, expires_at=expires_at)

    async def actor_from_headers(self, authorization: str | None, guest_session_token: str | None) -> Actor:
        actor = await self.verify_bearer(authorization)
        if actor:
            return actor
        if not guest_session_token:
            raise ApiError("missing_guest_session", "Start a guest session or sign in.", 401)
        token_hash = self._hash_secret(guest_session_token)
        rows = await self.select(
            "guest_sessions",
            {
                "select": "id,expires_at",
                "token_hash": f"eq.{token_hash}",
                "expires_at": f"gt.{datetime.now(UTC).isoformat()}",
                "limit": "1",
            },
        )
        if not rows:
            raise ApiError("guest_session_expired", "Your guest session has expired. Start a new one.", 401)
        return Actor(actor_type="guest", guest_session_id=rows[0]["id"])

    async def select(self, table: str, params: dict[str, str]) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{self.rest_url}/{table}", headers=self.service_headers, params=params)
        self._raise_for_supabase_error(response)
        return response.json()

    async def insert(self, table: str, payload: dict[str, Any] | list[dict[str, Any]]) -> list[dict[str, Any]]:
        headers = {**self.service_headers, "prefer": "return=representation"}
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(f"{self.rest_url}/{table}", headers=headers, json=payload)
        self._raise_for_supabase_error(response)
        return response.json()

    async def upsert(self, table: str, payload: dict[str, Any], on_conflict: str) -> list[dict[str, Any]]:
        headers = {**self.service_headers, "prefer": "resolution=merge-duplicates,return=representation"}
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{self.rest_url}/{table}",
                headers=headers,
                params={"on_conflict": on_conflict},
                json=payload,
            )
        self._raise_for_supabase_error(response)
        return response.json()

    async def update(self, table: str, row_id: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        headers = {**self.service_headers, "prefer": "return=representation"}
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.patch(
                f"{self.rest_url}/{table}",
                headers=headers,
                params={"id": f"eq.{row_id}"},
                json=payload,
            )
        self._raise_for_supabase_error(response)
        return response.json()

    async def delete(self, table: str, row_id: str) -> None:
        headers = {**self.service_headers, "prefer": "return=minimal"}
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.delete(
                f"{self.rest_url}/{table}",
                headers=headers,
                params={"id": f"eq.{row_id}"},
            )
        self._raise_for_supabase_error(response)

    async def storage_upload(self, path: str, data: bytes, content_type: str) -> None:
        headers = {
            "apikey": self.settings.supabase_service_role_key,
            "authorization": f"Bearer {self.settings.supabase_service_role_key}",
            "content-type": content_type,
            "x-upsert": "false",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.storage_url}/object/{self.settings.supabase_storage_bucket}/{path}",
                headers=headers,
                content=data,
            )
        self._raise_for_supabase_error(response)

    async def storage_download(self, path: str) -> bytes:
        headers = {
            "apikey": self.settings.supabase_service_role_key,
            "authorization": f"Bearer {self.settings.supabase_service_role_key}",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.storage_url}/object/{self.settings.supabase_storage_bucket}/{path}",
                headers=headers,
            )
        self._raise_for_supabase_error(response)
        return response.content

    async def storage_delete(self, paths: list[str]) -> None:
        if not paths:
            return
        headers = {**self.service_headers, "prefer": "return=minimal"}
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request(
                "DELETE",
                f"{self.storage_url}/object/{self.settings.supabase_storage_bucket}",
                headers=headers,
                json={"prefixes": paths},
            )
        self._raise_for_supabase_error(response)

    async def storage_signed_url(self, path: str, expires_in: int = 300, download: bool = False) -> str:
        headers = self.service_headers
        payload: dict[str, Any] = {"expiresIn": expires_in}
        if download:
            payload["download"] = True
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{self.storage_url}/object/sign/{self.settings.supabase_storage_bucket}/{path}",
                headers=headers,
                json=payload,
            )
        self._raise_for_supabase_error(response)
        body = response.json()
        signed_url = body.get("signedURL") or body.get("signedUrl") or body.get("signed_url")
        if not signed_url:
            raise ApiError("signed_url_failed", "Unable to create a playback URL.", 502)
        if signed_url.startswith("http"):
            return signed_url
        return f"{self.settings.supabase_url.rstrip('/')}/storage/v1{signed_url}"

    async def rpc(self, function_name: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        headers = {**self.service_headers, "prefer": "return=representation"}
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(f"{self.rest_url}/rpc/{function_name}", headers=headers, json=payload)
        self._raise_for_supabase_error(response)
        return response.json()

    def _raise_for_supabase_error(self, response: httpx.Response) -> None:
        if response.is_success:
            return
        try:
            detail = response.json()
        except ValueError:
            detail = {"message": response.text[:500]}
        raise ApiError(
            "supabase_request_failed",
            "A database operation failed. Try again shortly.",
            502,
            {"supabase": str(detail)[:500]},
        )
