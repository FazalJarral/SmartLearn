import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from worker.config import get_settings
from worker.scene_sanitizer import sanitize_scene
from worker.supabase_client import WorkerSupabaseClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("smartlearn.worker")


def transcript_path(asset: dict[str, Any]) -> str:
    return f"packages/{asset['package_id']}/video/{asset['id']}/transcript.txt"


def build_transcript(asset: dict[str, Any]) -> bytes:
    scenes = [sanitize_scene(scene) for scene in asset.get("scenes", [])]
    lines = [asset.get("plan_title") or "SmartLearn Video Plan", "", asset.get("narration") or ""]
    for index, scene in enumerate(scenes, start=1):
        lines.extend(["", f"Scene {index}: {scene['template']}", *scene["text"]])
    return "\n".join(lines).strip().encode("utf-8")


async def next_video_asset(client: WorkerSupabaseClient) -> dict[str, Any] | None:
    rows = await client.select(
        "video_assets",
        {
            "select": "id,package_id,status,plan_title,narration,scenes",
            "status": "eq.content_ready",
            "order": "created_at.asc",
            "limit": "1",
        },
    )
    return rows[0] if rows else None


async def process_video_asset(client: WorkerSupabaseClient, asset: dict[str, Any]) -> None:
    await client.update_by_id(
        "video_assets",
        asset["id"],
        {
            "status": "rendering_video",
            "user_message": "Preparing transcript and render assets.",
            "updated_at": datetime.now(UTC).isoformat(),
        },
    )
    try:
        path = transcript_path(asset)
        await client.storage_upload(path, build_transcript(asset), "text/plain")
        await client.update_by_id(
            "video_assets",
            asset["id"],
            {
                "status": "partial_success",
                "transcript_storage_path": path,
                "narration_available": False,
                "user_message": "Study material is ready. Video rendering is not enabled for this deployment.",
                "diagnostic_detail": "Worker persisted the validated video transcript; no renderer is configured.",
                "updated_at": datetime.now(UTC).isoformat(),
            },
        )
    except Exception as exc:
        await client.update_by_id(
            "video_assets",
            asset["id"],
            {
                "status": "failed",
                "error_code": "video_worker_failed",
                "user_message": "Video preparation failed. Retry from the document page.",
                "diagnostic_detail": str(exc)[:500],
                "updated_at": datetime.now(UTC).isoformat(),
            },
        )
        raise


async def run_once(client: WorkerSupabaseClient) -> bool:
    asset = await next_video_asset(client)
    if not asset:
        return False
    logger.info("processing video_asset=%s package=%s", asset["id"], asset["package_id"])
    await process_video_asset(client, asset)
    logger.info("processed video_asset=%s", asset["id"])
    return True


async def serve() -> None:
    settings = get_settings()
    client = WorkerSupabaseClient(settings)
    logger.info("SmartLearn worker started")
    while True:
        processed = await run_once(client)
        if not processed:
            await asyncio.sleep(settings.worker_poll_interval_seconds)


def main() -> None:
    asyncio.run(serve())


if __name__ == "__main__":
    main()
