import asyncio
import logging
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from worker.config import get_settings
from worker.scene_sanitizer import sanitize_scene
from worker.supabase_client import WorkerSupabaseClient
from worker.video_renderer import render_video, video_path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("smartlearn.worker")


def transcript_path(asset: dict[str, Any]) -> str:
    return f"packages/{asset['package_id']}/video/{asset['id']}/transcript.txt"


def build_transcript(asset: dict[str, Any]) -> bytes:
    scenes = [sanitize_scene(scene) for scene in asset.get("scenes", [])]
    lines = [asset.get("plan_title") or "SmartLearn Video Plan", "", asset.get("narration") or ""]
    for index, scene in enumerate(scenes, start=1):
        lines.extend(
            [
                "",
                f"Scene {index}: {scene['heading']} ({scene['template'].replace('_', ' ')})",
                scene["narration"],
                "Visuals: " + ", ".join(scene["visual_elements"]),
            ]
        )
    return "\n".join(lines).strip().encode("utf-8")


async def next_video_asset(
    client: WorkerSupabaseClient, lease_seconds: int = 300
) -> dict[str, Any] | None:
    rows = await client.select(
        "video_assets",
        {
            "select": "id,package_id,status,plan_title,narration,scenes",
            "status": "eq.content_ready",
            "order": "created_at.asc",
            "limit": "1",
        },
    )
    if rows:
        return rows[0]

    # If the container was killed (for example by an OOM), its exception handler
    # never runs. Reclaim the abandoned render once its lease has expired.
    lease_cutoff = datetime.now(UTC) - timedelta(seconds=lease_seconds)
    stale_rows = await client.select(
        "video_assets",
        {
            "select": "id,package_id,status,plan_title,narration,scenes",
            "status": "eq.rendering_video",
            "updated_at": f"lt.{lease_cutoff.isoformat()}",
            "order": "updated_at.asc",
            "limit": "1",
        },
    )
    if stale_rows:
        logger.warning("reclaiming stale video_asset=%s", stale_rows[0]["id"])
        return stale_rows[0]
    return None


async def process_video_asset(client: WorkerSupabaseClient, asset: dict[str, Any]) -> None:
    await client.update_by_id(
        "video_assets",
        asset["id"],
        {
            "status": "rendering_video",
            "user_message": "Animating the concept with Manim.",
            "updated_at": datetime.now(UTC).isoformat(),
        },
    )
    try:
        path = transcript_path(asset)
        await client.storage_upload(path, build_transcript(asset), "text/plain")
        with tempfile.TemporaryDirectory() as directory:
            settings = get_settings()
            rendered = render_video(
                asset,
                output_dir=Path(directory),
                pixel_width=settings.video_pixel_width,
                pixel_height=settings.video_pixel_height,
                frame_rate=settings.video_frame_rate,
            )
            mp4_path = video_path(asset)
            await client.storage_upload(mp4_path, rendered.path.read_bytes(), "video/mp4")
        await client.update_by_id(
            "video_assets",
            asset["id"],
            {
                "status": "completed",
                "video_storage_path": mp4_path,
                "transcript_storage_path": path,
                "duration_seconds": rendered.duration_seconds,
                "narration_available": False,
                "error_code": None,
                "user_message": "Video is ready.",
                "diagnostic_detail": "Rendered an animated Manim explainer from the safe scene plan.",
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
    asset = await next_video_asset(client, get_settings().job_lease_seconds)
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
        try:
            processed = await run_once(client)
        except Exception:
            logger.exception("video job failed")
            processed = False
        if not processed:
            await asyncio.sleep(settings.worker_poll_interval_seconds)


def main() -> None:
    asyncio.run(serve())


if __name__ == "__main__":
    main()
