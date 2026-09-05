import pytest

from worker.scene_sanitizer import sanitize_scene


def test_sanitizes_scene_text():
    scene = sanitize_scene({"template": "title", "text": ["<b>Hello</b>"], "duration_seconds": 99})
    assert scene["text"] == ["&lt;b&gt;Hello&lt;/b&gt;"]
    assert scene["duration_seconds"] == 12


def test_rejects_unknown_template():
    with pytest.raises(ValueError):
        sanitize_scene({"template": "python", "text": ["run code"]})
