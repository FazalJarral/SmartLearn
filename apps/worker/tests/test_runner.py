import asyncio
import shutil
from pathlib import Path

import pytest

from worker.runner import build_transcript, next_video_asset, transcript_path
from worker.video_renderer import render_video, video_path, wrap_text


def test_transcript_path_is_package_scoped():
    asset = {"id": "asset-1", "package_id": "package-1"}
    assert transcript_path(asset) == "packages/package-1/video/asset-1/transcript.txt"


def test_build_transcript_sanitizes_scene_text():
    asset = {
        "plan_title": "Intro",
        "narration": "Welcome.",
        "scenes": [{"template": "intro", "heading": "Intro", "visual_elements": ["<unsafe>", "Question"], "duration_seconds": 6}],
    }
    transcript = build_transcript(asset).decode("utf-8")
    assert "Intro" in transcript
    assert "&lt;unsafe&gt;" in transcript


def test_video_path_is_package_scoped():
    asset = {"id": "asset-1", "package_id": "package-1"}
    assert video_path(asset) == "packages/package-1/video/asset-1/study-video.mp4"


def test_wrap_text_keeps_long_lines_bounded():
    lines = wrap_text("This is a fairly long sentence that should be split across multiple lines.", width=24)
    assert len(lines) > 1
    assert all(len(line) <= 24 for line in lines)


def test_next_video_asset_reclaims_an_expired_render_lease():
    stale_asset = {"id": "stale-asset", "status": "rendering_video"}

    class FakeClient:
        def __init__(self):
            self.params = []

        async def select(self, _table, params):
            self.params.append(params)
            return [] if len(self.params) == 1 else [stale_asset]

    client = FakeClient()
    result = asyncio.run(next_video_asset(client, lease_seconds=120))

    assert result == stale_asset
    assert client.params[0]["status"] == "eq.content_ready"
    assert client.params[1]["status"] == "eq.rendering_video"
    assert client.params[1]["updated_at"].startswith("lt.")


@pytest.mark.skipif(shutil.which("manim") is None, reason="Manim is not installed")
def test_render_video_creates_mp4(tmp_path: Path):
    asset = {
        "id": "asset-1",
        "package_id": "package-1",
        "scenes": [{"template": "intro", "heading": "Intro", "visual_elements": ["Intro", "Welcome"], "duration_seconds": 6}],
    }

    rendered = render_video(asset, tmp_path)

    assert rendered.path.exists()
    assert rendered.path.suffix == ".mp4"
    assert rendered.duration_seconds == 6
