from __future__ import annotations

import html
import subprocess
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from PIL import Image, ImageDraw, ImageFont

from app.core.config import Settings

WIDTH = 1280
HEIGHT = 720
MAX_VIDEO_SECONDS = 60
MAX_NARRATION_WORDS = 105
BACKGROUND = "#f6f7f2"
INK = "#17201c"
SAGE = "#5d7f69"
MIST = "#dfe6dd"
VALID_TEMPLATES = {"title", "bullet_list", "comparison", "process", "definition"}


@dataclass(frozen=True)
class RenderedVideo:
    path: Path
    duration_seconds: int
    narration_available: bool


def transcript_path(asset: dict[str, Any]) -> str:
    return f"packages/{asset['package_id']}/video/{asset['id']}/transcript.txt"


def video_path(asset: dict[str, Any]) -> str:
    return f"packages/{asset['package_id']}/video/{asset['id']}/study-video.mp4"


def sanitize_scene(scene: dict[str, Any]) -> dict[str, Any]:
    template = scene.get("template") if scene.get("template") in VALID_TEMPLATES else "definition"
    text = [html.escape(str(item))[:180] for item in scene.get("text", [])[:6] if str(item).strip()]
    if not text:
        text = ["SmartLearn"]
    try:
        duration = int(scene.get("duration_seconds", 6))
    except (TypeError, ValueError):
        duration = 6
    return {
        "template": template,
        "text": text,
        "narration": str(scene.get("narration", "")).strip()[:500],
        "duration_seconds": min(max(duration, 3), 12),
    }


def scene_narration(asset: dict[str, Any]) -> str:
    scenes = [sanitize_scene(scene) for scene in asset.get("scenes", [])[:4]]
    narration_parts = [scene["narration"] for scene in scenes if scene.get("narration")]
    if not narration_parts:
        narration_parts = [str(asset.get("narration", ""))]
    words = " ".join(narration_parts).split()
    return " ".join(words[:MAX_NARRATION_WORDS])


def build_transcript(asset: dict[str, Any]) -> bytes:
    scenes = [sanitize_scene(scene) for scene in asset.get("scenes", [])]
    lines = [asset.get("plan_title") or "SmartLearn Video Plan", "", scene_narration(asset)]
    for index, scene in enumerate(scenes, start=1):
        lines.extend(["", f"Scene {index}: {scene['template']}", scene["narration"], *scene["text"]])
    return "\n".join(lines).strip().encode("utf-8")


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def wrap_text(text: str, width: int = 42) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines() or [text]:
        lines.extend(textwrap.wrap(raw_line.strip(), width=width) or [""])
    return lines


def draw_scene(scene: dict[str, Any], index: int, total: int, output_path: Path) -> None:
    sanitized = sanitize_scene(scene)
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    title_font = _font(54, bold=True)
    body_font = _font(34)
    meta_font = _font(24)

    draw.rectangle((0, 0, WIDTH, 88), fill=INK)
    draw.text((56, 28), "SmartLearn", fill="white", font=meta_font)
    draw.text((WIDTH - 190, 28), f"{index}/{total}", fill=MIST, font=meta_font)

    draw.rounded_rectangle((56, 130, WIDTH - 56, HEIGHT - 64), radius=24, fill="white", outline=MIST, width=2)
    title = sanitized["text"][0]
    draw.text((96, 172), title, fill=INK, font=title_font)

    y = 280
    for item in sanitized["text"][1:] or sanitized["text"][:1]:
        for line_index, line in enumerate(wrap_text(str(item), width=48)):
            prefix = "- " if line_index == 0 and sanitized["template"] in {"bullet_list", "process"} else "  "
            draw.text((112, y), f"{prefix}{line}", fill=INK, font=body_font)
            y += 46
            if y > HEIGHT - 150:
                break
        y += 12
        if y > HEIGHT - 150:
            break

    draw.rectangle((96, HEIGHT - 116, WIDTH - 96, HEIGHT - 108), fill=MIST)
    draw.rectangle((96, HEIGHT - 116, 96 + int((WIDTH - 192) * index / total), HEIGHT - 108), fill=SAGE)
    image.save(output_path)


def synthesize_voiceover(settings: Settings, text: str, output_path: Path) -> Path | None:
    if settings.tts_provider.lower() != "openai":
        return None
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required for voiceover generation")
    if not text.strip():
        return None

    response = httpx.post(
        "https://api.openai.com/v1/audio/speech",
        headers={"authorization": f"Bearer {settings.openai_api_key}"},
        json={
            "model": settings.tts_model,
            "voice": settings.tts_voice,
            "input": text,
            "response_format": "mp3",
        },
        timeout=60,
    )
    if not response.is_success:
        raise RuntimeError(f"OpenAI TTS failed: {response.text[:500]}")
    output_path.write_bytes(response.content)
    return output_path


def render_video(asset: dict[str, Any], output_dir: Path, settings: Settings | None = None) -> RenderedVideo:
    scenes = [sanitize_scene(scene) for scene in asset.get("scenes", [])[:4]]
    if not scenes:
        raise RuntimeError("video asset has no scenes")

    output_dir.mkdir(parents=True, exist_ok=True)
    concat_path = output_dir / "concat.txt"
    silent_video_file = output_dir / "study-video-silent.mp4"
    video_file = output_dir / "study-video.mp4"
    concat_lines: list[str] = []
    total_duration = 0

    for index, scene in enumerate(scenes, start=1):
        image_path = output_dir / f"scene-{index:02d}.png"
        draw_scene(scene, index, len(scenes), image_path)
        duration = int(scene["duration_seconds"])
        total_duration += duration
        concat_lines.extend([f"file '{image_path.as_posix()}'", f"duration {duration}"])
    concat_lines.append(f"file '{(output_dir / f'scene-{len(scenes):02d}.png').as_posix()}'")
    concat_path.write_text("\n".join(concat_lines), encoding="utf-8")

    result = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_path),
            "-vf",
            "format=yuv420p",
            "-movflags",
            "+faststart",
            "-r",
            "30",
            str(silent_video_file),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-500:] or "ffmpeg failed")

    voiceover_path = None
    if settings:
        voiceover_path = synthesize_voiceover(settings, scene_narration(asset), output_dir / "voiceover.mp3")
    if not voiceover_path:
        silent_video_file.replace(video_file)
        return RenderedVideo(
            path=video_file,
            duration_seconds=min(total_duration, MAX_VIDEO_SECONDS),
            narration_available=False,
        )

    result = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(silent_video_file),
            "-i",
            str(voiceover_path),
            "-t",
            str(MAX_VIDEO_SECONDS),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-shortest",
            "-movflags",
            "+faststart",
            str(video_file),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-500:] or "ffmpeg audio mux failed")
    return RenderedVideo(
        path=video_file,
        duration_seconds=min(total_duration, MAX_VIDEO_SECONDS),
        narration_available=True,
    )
