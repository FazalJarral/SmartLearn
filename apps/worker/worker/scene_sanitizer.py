from html import escape

MAX_TEXT_ITEMS = 6
MAX_TEXT_LENGTH = 160
ALLOWED_TEMPLATES = {"title", "bullet_list", "comparison", "process", "definition"}


def sanitize_scene(scene: dict) -> dict:
    template = scene.get("template")
    if template not in ALLOWED_TEMPLATES:
        raise ValueError("unsupported scene template")

    text_items = scene.get("text")
    if not isinstance(text_items, list) or not text_items:
        raise ValueError("scene text must be a non-empty list")

    clean_text = [escape(str(item)[:MAX_TEXT_LENGTH], quote=False) for item in text_items[:MAX_TEXT_ITEMS]]
    duration = int(scene.get("duration_seconds", 6))
    return {
        "template": template,
        "text": clean_text,
        "duration_seconds": min(max(duration, 3), 12),
    }
