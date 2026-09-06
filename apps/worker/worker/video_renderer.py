from __future__ import annotations

import subprocess
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from worker.scene_sanitizer import sanitize_scene

WIDTH = 1280
HEIGHT = 720
BACKGROUND = "#f6f7f2"
INK = "#17201c"
SAGE = "#5d7f69"
MIST = "#dfe6dd"


@dataclass(frozen=True)
class RenderedVideo:
    path: Path
    duration_seconds: int


def video_path(asset: dict[str, Any]) -> str:
    return f"packages/{asset['package_id']}/video/{asset['id']}/study-video.mp4"


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
        wrapped = textwrap.wrap(raw_line.strip(), width=width) or [""]
        lines.extend(wrapped)
    return lines


def scene_title(scene: dict[str, Any], index: int) -> str:
    template = str(scene.get("template", "Scene")).replace("_", " ").title()
    if scene.get("text"):
        return str(scene["text"][0])[:80]
    return f"Scene {index}: {template}"


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
    draw.text((96, 172), scene_title(sanitized, index), fill=INK, font=title_font)

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
    progress_width = int((WIDTH - 192) * index / total)
    draw.rectangle((96, HEIGHT - 116, 96 + progress_width, HEIGHT - 108), fill=SAGE)
    image.save(output_path)


def render_video(asset: dict[str, Any], output_dir: Path) -> RenderedVideo:
    scenes = [sanitize_scene(scene) for scene in asset.get("scenes", [])]
    if not scenes:
        raise RuntimeError("video asset has no scenes")

    output_dir.mkdir(parents=True, exist_ok=True)
    concat_path = output_dir / "concat.txt"
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

    command = [
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
        str(video_file),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-500:] or "ffmpeg failed")

    return RenderedVideo(path=video_file, duration_seconds=total_duration)
