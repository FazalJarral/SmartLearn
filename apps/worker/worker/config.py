from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = Field("local", alias="ENVIRONMENT")
    supabase_url: str = Field("", alias="SUPABASE_URL")
    supabase_service_role_key: str = Field("", alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_storage_bucket: str = Field("smartlearn-private", alias="SUPABASE_STORAGE_BUCKET")
    worker_poll_interval_seconds: int = Field(5, alias="WORKER_POLL_INTERVAL_SECONDS")
    job_lease_seconds: int = Field(300, alias="JOB_LEASE_SECONDS")
    worker_batch_size: int = Field(1, alias="WORKER_BATCH_SIZE")
    worker_id: str = Field("smartlearn-worker", alias="WORKER_ID")
    video_pixel_width: int = Field(854, alias="VIDEO_PIXEL_WIDTH")
    video_pixel_height: int = Field(480, alias="VIDEO_PIXEL_HEIGHT")
    video_frame_rate: int = Field(15, alias="VIDEO_FRAME_RATE")

    def runtime_errors(self) -> list[str]:
        errors: list[str] = []
        if not self.supabase_url:
            errors.append("SUPABASE_URL is required")
        if not self.supabase_service_role_key:
            errors.append("SUPABASE_SERVICE_ROLE_KEY is required")
        return errors


@lru_cache
def get_settings() -> WorkerSettings:
    return WorkerSettings()
