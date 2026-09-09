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


class SimpleDefinition(SourcePagesMixin):
    term: str = Field(min_length=1, max_length=120)
    definition: str = Field(min_length=1, max_length=500)
    example: str | None = Field(default=None, max_length=500)


class Summary(BaseModel):
    overview: str = Field(min_length=1, max_length=1500)
    key_points: list[KeyPoint] = Field(min_length=5, max_length=15)
    definitions: list[SimpleDefinition] = Field(min_length=3, max_length=30)


class LearningResource(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    resource_type: Literal["article", "video", "course", "practice", "book"]
    search_query: str = Field(min_length=3, max_length=240)
    why_it_helps: str = Field(min_length=1, max_length=400)


class Topic(SourcePagesMixin):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=500)
    further_learning: list[LearningResource] = Field(min_length=1, max_length=3)


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
    template: Literal[
        "intro", "concept_map", "comparison", "process", "cause_effect", "worked_example", "recap"
    ]
    heading: str = Field(min_length=1, max_length=120)
    visual_elements: list[str] = Field(min_length=2, max_length=6)
    connection_label: str | None = Field(default=None, max_length=80)
    narration: str = Field(min_length=1, max_length=800)
    duration_seconds: int = Field(ge=6, le=20)


class VideoPlan(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    narration: str = Field(min_length=1, max_length=1800)
    scenes: list[VideoScene] = Field(min_length=4, max_length=6)


class StudyPackage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    title: str = Field(min_length=1, max_length=160)
    summary: Summary
    topics: list[Topic] = Field(min_length=3, max_length=20)
    flashcards: list[Flashcard] = Field(min_length=8, max_length=20)
    quiz: list[QuizQuestion] = Field(min_length=5, max_length=10)
    video: VideoPlan
