import shutil
from pathlib import Path

import pytest

from worker.runner import build_transcript, transcript_path
from worker.video_renderer import render_video, video_path, wrap_text


def test_transcript_path_is_package_scoped():
    asset = {"id": "asset-1", "package_id": "package-1"}
    assert transcript_path(asset) == "packages/package-1/video/asset-1/transcript.txt"


def test_build_transcript_sanitizes_scene_text():
    asset = {
        "plan_title": "Intro",
        "narration": "Welcome.",
        "scenes": [{"template": "title", "text": ["<unsafe>"], "duration_seconds": 6}],
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


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed")
def test_render_video_creates_mp4(tmp_path: Path):
    asset = {
        "id": "asset-1",
        "package_id": "package-1",
        "scenes": [{"template": "title", "text": ["Intro", "Welcome"], "duration_seconds": 3}],
    }

    rendered = render_video(asset, tmp_path)

    assert rendered.path.exists()
    assert rendered.path.suffix == ".mp4"
    assert rendered.duration_seconds == 3
