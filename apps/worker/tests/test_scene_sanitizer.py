import pytest

from worker.scene_sanitizer import sanitize_scene


def test_sanitizes_scene_text():
    scene = sanitize_scene(
        {
            "template": "intro",
            "heading": "Hello",
            "visual_elements": ["<b>Hello</b>", "Question"],
            "duration_seconds": 99,
        }
    )
    assert scene["visual_elements"] == ["&lt;b&gt;Hello&lt;/b&gt;", "Question"]
    assert scene["duration_seconds"] == 20


def test_rejects_unknown_template():
    with pytest.raises(ValueError):
        sanitize_scene({"template": "python", "visual_elements": ["run code"]})
