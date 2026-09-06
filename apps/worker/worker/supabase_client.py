from __future__ import annotations

from typing import Any

import httpx

from worker.config import WorkerSettings


class WorkerSupabaseClient:
    def __init__(self, settings: WorkerSettings):
        if errors := settings.runtime_errors():
            raise RuntimeError("; ".join(errors))
        self.settings = settings
        self.rest_url = f"{settings.supabase_url.rstrip('/')}/rest/v1"
        self.storage_url = f"{settings.supabase_url.rstrip('/')}/storage/v1"

    @property
    def headers(self) -> dict[str, str]:
        return {
            "apikey": self.settings.supabase_service_role_key,
            "authorization": f"Bearer {self.settings.supabase_service_role_key}",
            "content-type": "application/json",
        }

    async def select(self, table: str, params: dict[str, str]) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(f"{self.rest_url}/{table}", headers=self.headers, params=params)
        self._raise_for_error(response)
        return response.json()

    async def update_by_id(self, table: str, row_id: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        headers = {**self.headers, "prefer": "return=representation"}
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.patch(
                f"{self.rest_url}/{table}",
                headers=headers,
                params={"id": f"eq.{row_id}"},
                json=payload,
            )
        self._raise_for_error(response)
        return response.json()

    async def storage_upload(self, path: str, data: bytes, content_type: str, upsert: bool = True) -> None:
        headers = {
            "apikey": self.settings.supabase_service_role_key,
            "authorization": f"Bearer {self.settings.supabase_service_role_key}",
            "content-type": content_type,
            "x-upsert": "true" if upsert else "false",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.storage_url}/object/{self.settings.supabase_storage_bucket}/{path}",
                headers=headers,
                content=data,
            )
        self._raise_for_error(response)

    def _raise_for_error(self, response: httpx.Response) -> None:
        if response.is_success:
            return
        try:
            detail = response.json()
        except ValueError:
            detail = response.text[:500]
        raise RuntimeError(f"Supabase request failed: {detail}")
