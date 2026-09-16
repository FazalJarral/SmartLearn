import shutil
from pathlib import Path

import pytest

from app.core.config import Settings
from app.services.video_rendering import render_video, scene_narration


def test_scene_narration_uses_scene_scripts_and_caps_words():
    asset = {
        "narration": "fallback narration",
        "scenes": [
            {"template": "definition", "text": ["One"], "narration": " ".join(["word"] * 90), "duration_seconds": 12},
            {"template": "definition", "text": ["Two"], "narration": " ".join(["more"] * 90), "duration_seconds": 12},
        ],
    }

    narration = scene_narration(asset)

    assert len(narration.split()) == 180
    assert "fallback" not in narration


@pytest.mark.skipif(shutil.which("manim") is None, reason="Manim is not installed")
def test_render_video_without_tts_creates_silent_mp4(tmp_path: Path):
    asset = {
        "id": "asset-1",
        "package_id": "package-1",
        "scenes": [
            {
                "template": "concept_map",
                "heading": "Concept",
                "visual_elements": ["Concept", "Quick explanation"],
                "narration": "This concept matters because it anchors the rest of the lesson.",
                "duration_seconds": 6,
            }
        ],
    }

    rendered = render_video(asset, tmp_path)

    assert rendered.path.exists()
    assert rendered.duration_seconds == 6
    assert rendered.narration_available is False


@pytest.mark.skipif(shutil.which("manim") is None, reason="Manim is not installed")
def test_render_video_falls_back_to_silent_when_tts_misconfigured(tmp_path: Path):
    asset = {
        "id": "asset-1",
        "package_id": "package-1",
        "scenes": [
            {
                "template": "concept_map",
                "heading": "Concept",
                "visual_elements": ["Concept", "Quick explanation"],
                "narration": "This concept matters because it anchors the rest of the lesson.",
                "duration_seconds": 6,
            }
        ],
    }
    settings = Settings(TTS_PROVIDER="openai", OPENAI_API_KEY="")

    rendered = render_video(asset, tmp_path, settings)

    assert rendered.path.exists()
    assert rendered.narration_available is False
