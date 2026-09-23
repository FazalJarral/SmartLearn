import shutil
from pathlib import Path

import pytest

from app.core.config import Settings
from app.services import video_rendering
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


def test_synthesize_voiceover_falls_back_to_google_when_piper_fails(tmp_path: Path, monkeypatch):
    def fake_piper(*_args):
        raise RuntimeError("piper boom")

    def fake_google(settings, text, output_path):
        output_path.write_bytes(b"fake-audio")
        return output_path

    monkeypatch.setattr(video_rendering, "_synthesize_piper", fake_piper)
    monkeypatch.setattr(video_rendering, "_synthesize_google", fake_google)
    settings = Settings(TTS_PROVIDER="piper", GOOGLE_TTS_API_KEY="key")
    output_path = tmp_path / "voiceover.audio"

    result = video_rendering.synthesize_voiceover(settings, "hello world", output_path)

    assert result == output_path
    assert output_path.read_bytes() == b"fake-audio"


def test_synthesize_voiceover_raises_combined_error_when_both_fail(tmp_path: Path, monkeypatch):
    def fake_piper(*_args):
        raise RuntimeError("piper boom")

    def fake_google(*_args):
        raise RuntimeError("google boom")

    monkeypatch.setattr(video_rendering, "_synthesize_piper", fake_piper)
    monkeypatch.setattr(video_rendering, "_synthesize_google", fake_google)
    settings = Settings(TTS_PROVIDER="piper", GOOGLE_TTS_API_KEY="key")
    output_path = tmp_path / "voiceover.audio"

    with pytest.raises(RuntimeError, match="piper boom.*google boom"):
        video_rendering.synthesize_voiceover(settings, "hello world", output_path)


def test_synthesize_voiceover_raises_piper_error_without_google_key(tmp_path: Path, monkeypatch):
    def fake_piper(*_args):
        raise RuntimeError("piper boom")

    monkeypatch.setattr(video_rendering, "_synthesize_piper", fake_piper)
    settings = Settings(TTS_PROVIDER="piper", GOOGLE_TTS_API_KEY="")
    output_path = tmp_path / "voiceover.audio"

    with pytest.raises(RuntimeError, match="piper boom"):
        video_rendering.synthesize_voiceover(settings, "hello world", output_path)
