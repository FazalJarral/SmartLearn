import asyncio
from typing import ClassVar

from app.core.config import Settings
from app.services import supabase_client
from app.services.supabase_client import SupabaseService


class _Response:
    is_success = True


class _AsyncClient:
    last_headers: ClassVar[dict[str, str]] = {}

    def __init__(self, **_kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def post(self, _url, *, headers, content):
        self.__class__.last_headers = headers
        assert content == b"artifact"
        return _Response()


def test_storage_upload_can_overwrite_retry_artifacts(monkeypatch) -> None:
    monkeypatch.setattr(supabase_client.httpx, "AsyncClient", _AsyncClient)
    settings = Settings(
        _env_file=None,
        SUPABASE_URL="https://example.supabase.co",
        SUPABASE_SERVICE_ROLE_KEY="service-key",
    )
    service = SupabaseService(settings)

    asyncio.run(service.storage_upload("video/transcript.txt", b"artifact", "text/plain", upsert=True))

    assert _AsyncClient.last_headers["x-upsert"] == "true"


def test_storage_upload_protects_source_files_by_default(monkeypatch) -> None:
    monkeypatch.setattr(supabase_client.httpx, "AsyncClient", _AsyncClient)
    settings = Settings(
        _env_file=None,
        SUPABASE_URL="https://example.supabase.co",
        SUPABASE_SERVICE_ROLE_KEY="service-key",
    )
    service = SupabaseService(settings)

    asyncio.run(service.storage_upload("sources/lesson.pdf", b"artifact", "application/pdf"))

    assert _AsyncClient.last_headers["x-upsert"] == "false"
