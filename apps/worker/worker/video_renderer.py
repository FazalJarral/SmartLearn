from __future__ import annotations

import shutil
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from worker.scene_sanitizer import sanitize_scene


@dataclass(frozen=True)
class RenderedVideo:
    path: Path
    duration_seconds: int


def video_path(asset: dict[str, Any]) -> str:
    return f"packages/{asset['package_id']}/video/{asset['id']}/study-video.mp4"


def wrap_text(text: str, width: int = 42) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines() or [text]:
        lines.extend(textwrap.wrap(raw_line.strip(), width=width) or [""])
    return lines


def render_video(asset: dict[str, Any], output_dir: Path) -> RenderedVideo:
    scenes = [sanitize_scene(scene) for scene in asset.get("scenes", [])[:6]]
    if not scenes:
        raise RuntimeError("video asset has no scenes")
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
        mob = Text(value, font_size=size, color=ink)
        if mob.width > max_width:
            mob.scale_to_fit_width(max_width)
        return mob

    def box(value: str, color=sage, fill=mint, width=2.2):
        shape = RoundedRectangle(width=width, height=1.2, corner_radius=0.18, color=color,
                                 fill_color=fill, fill_opacity=0.38)
        return VGroup(shape, label(value, 23, width - 0.35).move_to(shape))

    class SmartLearnExplainer(Scene):
        def construct(self):
            self.camera.background_color = background
            active = VGroup()
            for plan in scenes:
                if len(active):
                    self.play(FadeOut(active, shift=0.15 * UP), run_time=0.35)
                heading = label(plan["heading"], 34, 11.5).to_edge(UP, buff=0.38)
                underline = Line(LEFT * 2.2, RIGHT * 2.2, color=sage, stroke_width=5).next_to(
                    heading, DOWN, buff=0.14
                )
                self.play(Write(heading), Create(underline), run_time=0.55)
                visual, used = self.visual(plan)
                active = VGroup(heading, underline, visual)
                self.wait(max(0.2, plan["duration_seconds"] - used - 0.9))

        def visual(self, plan):
            items = plan["visual_elements"]
            relation = plan["connection_label"] or "connects to"
            kind = plan["template"]
            if kind == "intro":
                core = VGroup(Circle(1.25, color=sage, fill_color=mint, fill_opacity=0.5), label(items[0], 30, 2))
                core[1].move_to(core[0]); core.shift(0.3 * DOWN)
                orbit = Circle(2.15, color=mist).move_to(core)
                marker = Dot(orbit.point_at_angle(0), radius=0.13, color=gold)
                prompt = label(items[1], 23, 3.2).next_to(core, DOWN, buff=0.5)
                group = VGroup(orbit, core, marker, prompt)
                self.play(Create(orbit), GrowFromCenter(core), run_time=1)
                self.play(MoveAlongPath(marker, orbit), FadeIn(prompt, shift=UP), run_time=1.8)
                return group, 2.8
            if kind in {"process", "worked_example"}:
                boxes = VGroup(*[box(item, width=1.9) for item in items[:5]])
                boxes.arrange(RIGHT, buff=0.55).shift(0.3 * DOWN)
                arrows = VGroup(*[Arrow(boxes[i].get_right(), boxes[i + 1].get_left(), buff=0.08, color=sage)
                                  for i in range(len(boxes) - 1)])
                marker = Dot(boxes[0].get_center(), color=gold)
                group = VGroup(boxes, arrows, marker)
                self.play(LaggedStart(*[GrowFromCenter(b) for b in boxes], lag_ratio=0.12), run_time=1)
                self.play(LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.12), run_time=0.8)
                for target in boxes[1:]: self.play(marker.animate.move_to(target), run_time=0.3)
                return group, 1.8 + 0.3 * (len(boxes) - 1)
            if kind == "comparison":
                left = Circle(1.65, color=sage, fill_color=mint, fill_opacity=0.38).shift(1.15 * LEFT + 0.3 * DOWN)
                right = Circle(1.65, color=gold, fill_color="#f6d78f", fill_opacity=0.35).shift(1.15 * RIGHT + 0.3 * DOWN)
                lt = label(items[0], 26, 1.7).move_to(left).shift(0.75 * LEFT)
                rt = label(items[1], 26, 1.7).move_to(right).shift(0.75 * RIGHT)
                shared = label(relation, 19, 1.3).move_to((left.get_center() + right.get_center()) / 2)
                group = VGroup(left, right, lt, rt, shared)
                self.play(Create(left), FadeIn(lt, shift=RIGHT), run_time=0.8)
                self.play(Create(right), FadeIn(rt, shift=LEFT), run_time=0.8)
                self.play(FadeIn(shared), run_time=0.8)
                return group, 2.4
            if kind == "cause_effect":
                cause, effect = box(items[0], width=3.4), box(items[1], gold, "#f6d78f", 3.4)
                cause.shift(3 * LEFT + 0.3 * DOWN); effect.shift(3 * RIGHT + 0.3 * DOWN)
                arrow = CurvedArrow(cause.get_right(), effect.get_left(), angle=-0.35, color=sage)
                rel = label(relation, 20, 2.5).next_to(arrow, UP, buff=0.1)
                group = VGroup(cause, effect, arrow, rel)
                self.play(GrowFromCenter(cause), run_time=0.7)
                self.play(GrowArrow(arrow), FadeIn(rel), run_time=0.8)
                self.play(GrowFromCenter(effect), run_time=0.8)
                return group, 2.3
            core = VGroup(Circle(0.95, color=sage, fill_color=mint, fill_opacity=0.55), label(items[0], 25, 1.5))
            core[1].move_to(core[0])
            positions = [LEFT * 3.4 + UP, RIGHT * 3.4 + UP, LEFT * 2.8 + DOWN * 1.5,
                         RIGHT * 2.8 + DOWN * 1.5, DOWN * 2]
            nodes, arrows = VGroup(), VGroup()
            for item, position in zip(items[1:], positions):
                node = box(item, width=1.7).move_to(position); nodes.add(node)
                arrows.add(Arrow(core.get_center(), node.get_center(), buff=0.85, color=sage))
            rel = label(relation, 19, 2.8).next_to(core, DOWN, buff=0.2)
            group = VGroup(arrows, core, nodes, rel)
            self.play(GrowFromCenter(core), FadeIn(rel), run_time=0.7)
            self.play(LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.12), run_time=0.9)
            self.play(LaggedStart(*[GrowFromCenter(n) for n in nodes], lag_ratio=0.12), run_time=1)
            return group, 2.6

    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "study-video.mp4"
    with tempconfig({
        "pixel_width": 1280, "pixel_height": 720, "frame_rate": 30,
        "media_dir": str(output_dir / "manim-media"), "output_file": "study-video",
        "format": "mp4", "write_to_movie": True, "disable_caching": True, "verbosity": "WARNING",
    }):
        scene = SmartLearnExplainer(); scene.render()
        rendered = Path(scene.renderer.file_writer.movie_file_path)
    if not rendered.exists():
        raise RuntimeError("Manim did not produce an MP4")
    shutil.copyfile(rendered, output)
    return RenderedVideo(output, min(sum(scene["duration_seconds"] for scene in scenes), 90))
