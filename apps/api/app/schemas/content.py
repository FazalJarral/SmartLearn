from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SourcePagesMixin(BaseModel):
    source_pages: list[int] = Field(default_factory=list, max_length=20)

    @field_validator("source_pages")
    @classmethod
    def pages_are_positive(cls, pages: list[int]) -> list[int]:
        if any(page < 1 for page in pages):
            raise ValueError("source pages must be one-based")
        return sorted(set(pages))


class KeyPoint(SourcePagesMixin):
    heading: str = Field(min_length=1, max_length=120)
    explanation: str = Field(min_length=1, max_length=1000)


class Summary(BaseModel):
    overview: str = Field(min_length=1, max_length=1500)
    key_points: list[KeyPoint] = Field(min_length=5, max_length=15)


class Flashcard(SourcePagesMixin):
    id: UUID | None = None
    front: str = Field(min_length=1, max_length=280)
    back: str = Field(min_length=1, max_length=800)


class QuizQuestion(SourcePagesMixin):
    id: UUID | None = None
    question: str = Field(min_length=1, max_length=500)
    options: list[str] = Field(min_length=4, max_length=4)
    correct_option_index: int = Field(ge=0, le=3)
    explanation: str = Field(min_length=1, max_length=1000)

    @field_validator("options")
    @classmethod
    def options_are_bounded(cls, options: list[str]) -> list[str]:
        for option in options:
            if not option or len(option) > 240:
                raise ValueError("each option must be 1-240 characters")
        return options


class VideoScene(BaseModel):
    template: Literal["title", "bullet_list", "comparison", "process", "definition"]
    text: list[str] = Field(min_length=1, max_length=6)
    narration: str = Field(default="", max_length=500)
    duration_seconds: int = Field(ge=3, le=12)


class VideoPlan(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    narration: str = Field(min_length=1, max_length=1000)
    scenes: list[VideoScene] = Field(min_length=3, max_length=4)


class StudyPackage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    title: str = Field(min_length=1, max_length=160)
    summary: Summary
    flashcards: list[Flashcard] = Field(min_length=8, max_length=20)
    quiz: list[QuizQuestion] = Field(min_length=5, max_length=10)
    video: VideoPlan
