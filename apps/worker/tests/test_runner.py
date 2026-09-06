from worker.runner import build_transcript, transcript_path


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
