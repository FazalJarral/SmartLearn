from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.state import ProcessingStage
from app.schemas.content import StudyPackage


class GuestSessionResponse(BaseModel):
    guest_session_id: str
    expires_at: datetime


class UsageResponse(BaseModel):
    actor_type: str
    accepted_today: int
    daily_limit: int
    remaining: int
    resets_at_utc: datetime


class DocumentStatusResponse(BaseModel):
    document_id: UUID
    stage: ProcessingStage
    progress: int = Field(ge=0, le=100)
    message: str
    warnings: list[str] = Field(default_factory=list)
    error_code: str | None = None
    package_id: UUID | None = None


class DocumentListItem(BaseModel):
    id: UUID
    original_filename: str
    stage: ProcessingStage
    progress: int = Field(ge=0, le=100)
    created_at: datetime
    deleted_at: datetime | None = None
    package_id: UUID | None = None
    title: str | None = None


class LearningPackageResponse(BaseModel):
    id: UUID
    document_id: UUID
    content: StudyPackage
    video_asset_id: UUID | None = None
    video_status: ProcessingStage | None = None
    video_message: str | None = None
    video_available: bool = False
    transcript_available: bool = False


class SignedUrlResponse(BaseModel):
    url: str
    expires_in: int


class VideoRetryResponse(BaseModel):
    video_asset_id: UUID
    status: ProcessingStage
    message: str


class QuizAnswerIn(BaseModel):
    question_id: UUID
    selected_index: int = Field(ge=0, le=3)


class QuizAttemptResponse(BaseModel):
    id: UUID
    package_id: UUID
    score: int = Field(ge=0)
    total: int = Field(ge=0)
    started_at: datetime
    completed_at: datetime | None = None


class QuizAnswerResult(BaseModel):
    attempt_id: UUID
    question_id: UUID
    selected_index: int = Field(ge=0, le=3)
    correct_index: int = Field(ge=0, le=3)
    is_correct: bool
    explanation: str
    score: int = Field(ge=0)
    total: int = Field(ge=0)
