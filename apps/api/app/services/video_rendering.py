from __future__ import annotations

import html
import shutil
import subprocess
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from app.core.config import Settings

MAX_VIDEO_SECONDS = 90
MAX_NARRATION_WORDS = 180
VALID_TEMPLATES = {
    "intro", "concept_map", "comparison", "process", "cause_effect", "worked_example", "recap"
}


@dataclass(frozen=True)
class RenderedVideo:
    path: Path
    duration_seconds: int
    narration_available: bool


def transcript_path(asset: dict[str, Any]) -> str:
    return f"packages/{asset['package_id']}/video/{asset['id']}/transcript.txt"


def video_path(asset: dict[str, Any]) -> str:
    return f"packages/{asset['package_id']}/video/{asset['id']}/study-video.mp4"


def wrap_text(text: str, width: int = 42) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines() or [text]:
        lines.extend(textwrap.wrap(raw_line.strip(), width=width) or [""])
    return lines


def sanitize_scene(scene: dict[str, Any]) -> dict[str, Any]:
    legacy_templates = {"title": "intro", "definition": "concept_map", "bullet_list": "concept_map"}
    requested_template = legacy_templates.get(scene.get("template"), scene.get("template"))
    template = requested_template if requested_template in VALID_TEMPLATES else "concept_map"
    raw_elements = scene.get("visual_elements", scene.get("text", []))
    elements = [html.escape(str(item), quote=False)[:160] for item in raw_elements[:6] if str(item).strip()]
    if len(elements) < 2:
        elements = (elements + ["Example", "Result"])[:2]
    try:
        duration = int(scene.get("duration_seconds", 10))
    except (TypeError, ValueError):
        duration = 10
    return {
        "template": template,
        "heading": html.escape(str(scene.get("heading") or elements[0]), quote=False)[:120],
        "visual_elements": elements,
        "connection_label": html.escape(str(scene.get("connection_label") or ""), quote=False)[:80],
        "narration": str(scene.get("narration", "")).strip()[:800],
        "duration_seconds": min(max(duration, 6), 20),
    }


def scene_narration(asset: dict[str, Any]) -> str:
    scenes = [sanitize_scene(scene) for scene in asset.get("scenes", [])[:6]]
    parts = [scene["narration"] for scene in scenes if scene["narration"]]
    words = " ".join(parts or [str(asset.get("narration", ""))]).split()
    return " ".join(words[:MAX_NARRATION_WORDS])


def build_transcript(asset: dict[str, Any]) -> bytes:
    scenes = [sanitize_scene(scene) for scene in asset.get("scenes", [])]
    lines = [asset.get("plan_title") or "SmartLearn Explainer", "", scene_narration(asset)]
    for index, scene in enumerate(scenes, start=1):
        lines.extend([
            "", f"Scene {index}: {scene['heading']} ({scene['template'].replace('_', ' ')})",
            scene["narration"], "Visuals: " + ", ".join(scene["visual_elements"]),
        ])
    return "\n".join(lines).strip().encode("utf-8")


def _render_with_manim(plans: list[dict[str, Any]], output_dir: Path) -> Path:
    try:
        from manim import (
            DOWN,
            LEFT,
            RIGHT,
            UP,
            Arrow,
            Circle,
            Create,
            CurvedArrow,
            Dot,
            FadeIn,
            FadeOut,
            GrowArrow,
            GrowFromCenter,
            LaggedStart,
            Line,
            MoveAlongPath,
            ReplacementTransform,
            RoundedRectangle,
            Scene,
            Text,
            VGroup,
            Write,
            tempconfig,
        )
    except ImportError as exc:
        raise RuntimeError("Manim Community is required to render explainer videos") from exc

    ink, sage, mint, gold, mist, background = (
        "#17201c", "#5d7f69", "#b9d8c2", "#e8b44f", "#dfe6dd", "#f6f7f2"
    )

    def label(value: str, size: int = 26, max_width: float = 2.2):
        mob = Text(value, font_size=size, color=ink, line_spacing=0.9)
        if mob.width > max_width:
            mob.scale_to_fit_width(max_width)
        return mob

    def box_for(value: str, color=sage, fill=mint, width=2.2):
        shape = RoundedRectangle(width=width, height=1.2, corner_radius=0.18, color=color,
                                 fill_color=fill, fill_opacity=0.38)
        return VGroup(shape, label(value, 23, width - 0.35).move_to(shape))

    class SmartLearnExplainer(Scene):
        def construct(self):
            self.camera.background_color = background
            active = VGroup()
            for plan in plans:
                if len(active):
                    self.play(FadeOut(active, shift=0.15 * UP), run_time=0.35)
                heading = label(plan["heading"], 34, 11.5).to_edge(UP, buff=0.38)
                underline = Line(LEFT * 2.2, RIGHT * 2.2, color=sage, stroke_width=5)
                underline.next_to(heading, DOWN, buff=0.14)
                self.play(Write(heading), Create(underline), run_time=0.55)
                visual, used = self.build_visual(plan)
                active = VGroup(heading, underline, visual)
                self.wait(max(0.2, plan["duration_seconds"] - used - 0.9))

        def build_visual(self, plan):
            items, relation = plan["visual_elements"], plan["connection_label"] or "connects to"
            if plan["template"] == "intro":
                core = VGroup(Circle(1.25, color=sage, fill_color=mint, fill_opacity=0.5), label(items[0], 30, 2))
                core[1].move_to(core[0]); core.shift(0.3 * DOWN)
                orbit = Circle(2.15, color=mist).move_to(core)
                dot = Dot(orbit.point_at_angle(0), radius=0.13, color=gold)
                question = label(items[1], 23, 3.2).next_to(core, DOWN, buff=0.5)
                group = VGroup(orbit, core, dot, question)
                self.play(Create(orbit), GrowFromCenter(core), run_time=1)
                self.play(MoveAlongPath(dot, orbit), FadeIn(question, shift=UP), run_time=1.8)
                return group, 2.8

            if plan["template"] == "concept_map":
                core = VGroup(Circle(0.95, color=sage, fill_color=mint, fill_opacity=0.55), label(items[0], 25, 1.5))
                core[1].move_to(core[0])
                positions = [LEFT * 3.4 + UP, RIGHT * 3.4 + UP, LEFT * 2.8 + DOWN * 1.5,
                             RIGHT * 2.8 + DOWN * 1.5, DOWN * 2]
                nodes, arrows = VGroup(), VGroup()
                for item, position in zip(items[1:], positions):
                    node = VGroup(Circle(0.7, color=sage, fill_color="#ffffff", fill_opacity=1), label(item, 20, 1.15))
                    node[1].move_to(node[0]); node.move_to(position); nodes.add(node)
                    arrows.add(Arrow(core.get_center(), node.get_center(), buff=0.85, color=sage))
                rel = label(relation, 19, 2.8).next_to(core, DOWN, buff=0.2)
                group = VGroup(arrows, core, nodes, rel)
                self.play(GrowFromCenter(core), FadeIn(rel), run_time=0.7)
                self.play(LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.12), run_time=0.9)
                self.play(LaggedStart(*[GrowFromCenter(n) for n in nodes], lag_ratio=0.12), run_time=1)
                return group, 2.6

            if plan["template"] == "process":
                boxes = VGroup(*[box_for(item, width=1.9) for item in items[:5]])
                boxes.arrange(RIGHT, buff=0.55).shift(0.3 * DOWN)
                arrows = VGroup(*[Arrow(boxes[i].get_right(), boxes[i + 1].get_left(), buff=0.08, color=sage)
                                  for i in range(len(boxes) - 1)])
                marker = Dot(boxes[0].get_center(), color=gold)
                rel = label(relation, 19, 2.8).next_to(boxes, DOWN, buff=0.4)
                group = VGroup(boxes, arrows, marker, rel)
                self.play(LaggedStart(*[GrowFromCenter(b) for b in boxes], lag_ratio=0.12), run_time=1)
                self.play(LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.12), FadeIn(rel), run_time=0.8)
                for box in boxes[1:]: self.play(marker.animate.move_to(box), run_time=0.3)
                return group, 1.8 + 0.3 * (len(boxes) - 1)

            if plan["template"] == "comparison":
                left = Circle(1.65, color=sage, fill_color=mint, fill_opacity=0.38).shift(1.15 * LEFT + 0.3 * DOWN)
                right = Circle(1.65, color=gold, fill_color="#f6d78f", fill_opacity=0.35).shift(1.15 * RIGHT + 0.3 * DOWN)
                lt = label(items[0], 26, 1.7).move_to(left).shift(0.75 * LEFT)
                rt = label(items[1], 26, 1.7).move_to(right).shift(0.75 * RIGHT)
                shared = label(relation, 19, 1.35).move_to((left.get_center() + right.get_center()) / 2)
                extras = VGroup(*[label(x, 19, 2.4) for x in items[2:4]]).arrange(DOWN, buff=0.15)
                extras.next_to(VGroup(left, right), DOWN, buff=0.35)
                group = VGroup(left, right, lt, rt, shared, extras)
                self.play(Create(left), FadeIn(lt, shift=RIGHT), run_time=0.8)
                self.play(Create(right), FadeIn(rt, shift=LEFT), run_time=0.8)
                self.play(FadeIn(shared), FadeIn(extras), run_time=0.8)
                return group, 2.4

            if plan["template"] == "cause_effect":
                left, right = box_for(items[0], width=3.4), box_for(items[1], gold, "#f6d78f", 3.4)
                left.shift(3 * LEFT + 0.3 * DOWN); right.shift(3 * RIGHT + 0.3 * DOWN)
                arrow = CurvedArrow(left.get_right(), right.get_left(), angle=-0.35, color=sage)
                rel = label(relation, 20, 2.5).next_to(arrow, UP, buff=0.1)
                group = VGroup(left, right, arrow, rel)
                self.play(GrowFromCenter(left), run_time=0.7)
                self.play(GrowArrow(arrow), FadeIn(rel), run_time=0.8)
                self.play(GrowFromCenter(right), run_time=0.8)
                return group, 2.3

            if plan["template"] == "worked_example":
                sources = VGroup(*[box_for(item, width=1.8) for item in items[:-1]]).arrange(DOWN, buff=0.25)
                sources.shift(3 * LEFT + 0.3 * DOWN)
                target = box_for(items[-1], gold, "#f6d78f", 3).shift(3 * RIGHT + 0.3 * DOWN)
                arrow = Arrow(sources.get_right(), target.get_left(), buff=0.2, color=sage)
                group = VGroup(sources, arrow, target)
                self.play(LaggedStart(*[GrowFromCenter(s) for s in sources], lag_ratio=0.15), run_time=1)
                self.play(GrowArrow(arrow), run_time=0.6)
                ghost = sources.copy(); self.add(ghost)
                self.play(ReplacementTransform(ghost, target), run_time=1)
                return group, 2.6

            nodes = VGroup(*[VGroup(Dot(color=sage), label(item, 21, 2.5)) for item in items[:-1]])
            for node in nodes: node[1].next_to(node[0], RIGHT, buff=0.2)
            nodes.arrange(DOWN, aligned_edge=LEFT, buff=0.45).shift(3.4 * LEFT + 0.2 * DOWN)
            result = VGroup(Circle(1.15, color=sage, fill_color=mint, fill_opacity=0.5), label(items[-1], 26, 1.8))
            result[1].move_to(result[0]); result.shift(3 * RIGHT + 0.2 * DOWN)
            arrows = VGroup(*[Arrow(node.get_right(), result.get_left(), buff=0.25, color=sage) for node in nodes])
            group = VGroup(nodes, arrows, result)
            self.play(LaggedStart(*[FadeIn(n, shift=RIGHT) for n in nodes], lag_ratio=0.12), run_time=1)
            self.play(LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.1), run_time=0.8)
            self.play(GrowFromCenter(result), run_time=0.8)
            return group, 2.6

    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "study-video.mp4"
    with tempconfig({
        "pixel_width": 854, "pixel_height": 480, "frame_rate": 15,
        "media_dir": str(output_dir / "manim-media"), "output_file": "study-video",
        "format": "mp4", "write_to_movie": True, "disable_caching": True,
        "verbosity": "WARNING", "progress_bar": "none",
    }):
        scene = SmartLearnExplainer()
        scene.render()
        rendered = Path(scene.renderer.file_writer.movie_file_path)
    if not rendered.exists():
        raise RuntimeError("Manim did not produce an MP4")
    shutil.copyfile(rendered, output)
    return output


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
        json={"model": settings.tts_model, "voice": settings.tts_voice, "input": text, "response_format": "mp3"},
        timeout=60,
    )
    if not response.is_success:
        raise RuntimeError(f"OpenAI TTS failed: {response.text[:500]}")
    output_path.write_bytes(response.content)
    return output_path


def render_video(asset: dict[str, Any], output_dir: Path, settings: Settings | None = None) -> RenderedVideo:
    scenes = [sanitize_scene(scene) for scene in asset.get("scenes", [])[:6]]
    if not scenes:
        raise RuntimeError("video asset has no scenes")
    total_duration = min(sum(scene["duration_seconds"] for scene in scenes), MAX_VIDEO_SECONDS)
    video_file = _render_with_manim(scenes, output_dir)
    voiceover = synthesize_voiceover(settings, scene_narration(asset), output_dir / "voiceover.mp3") if settings else None
    if not voiceover:
        return RenderedVideo(video_file, total_duration, False)
    muxed = output_dir / "study-video-with-audio.mp4"
    result = subprocess.run([
        "ffmpeg", "-y", "-i", str(video_file), "-i", str(voiceover), "-t", str(MAX_VIDEO_SECONDS),
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-shortest",
        "-movflags", "+faststart", str(muxed),
    ], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-500:] or "ffmpeg audio mux failed")
    return RenderedVideo(muxed, total_duration, True)
