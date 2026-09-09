from html import escape

MAX_TEXT_ITEMS = 6
MAX_TEXT_LENGTH = 160
ALLOWED_TEMPLATES = {
    "intro",
    "concept_map",
    "comparison",
    "process",
    "cause_effect",
    "worked_example",
    "recap",
}


def sanitize_scene(scene: dict) -> dict:
    legacy_templates = {"title": "intro", "definition": "concept_map", "bullet_list": "concept_map"}
    template = legacy_templates.get(scene.get("template"), scene.get("template"))
    if template not in ALLOWED_TEMPLATES:
        raise ValueError("unsupported scene template")

    text_items = scene.get("visual_elements", scene.get("text"))
    if not isinstance(text_items, list) or not text_items:
        raise ValueError("scene visual_elements must be a non-empty list")

    clean_text = [escape(str(item)[:MAX_TEXT_LENGTH], quote=False) for item in text_items[:MAX_TEXT_ITEMS]]
    if len(clean_text) < 2:
        clean_text.append("Example")
    duration = int(scene.get("duration_seconds", 10))
    return {
        "template": template,
        "heading": escape(str(scene.get("heading") or clean_text[0])[:120], quote=False),
        "visual_elements": clean_text,
        "text": clean_text,
        "connection_label": escape(str(scene.get("connection_label") or "")[:80], quote=False),
        "narration": str(scene.get("narration") or "").strip()[:800],
        "duration_seconds": min(max(duration, 6), 20),
    }
