from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "local"
    cors_origins_raw: str = Field("http://localhost:5173", alias="API_CORS_ORIGINS")
    max_upload_bytes: int = Field(15 * 1024 * 1024, alias="MAX_UPLOAD_BYTES")
    max_pdf_pages: int = Field(20, alias="MAX_PDF_PAGES")
    guest_daily_upload_limit: int = Field(1, alias="GUEST_DAILY_UPLOAD_LIMIT")
    registered_daily_upload_limit: int = Field(5, alias="REGISTERED_DAILY_UPLOAD_LIMIT")
    supabase_url: str = Field("", alias="SUPABASE_URL")
    supabase_anon_key: str = Field("", alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: str = Field("", alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_storage_bucket: str = Field("smartlearn-private", alias="SUPABASE_STORAGE_BUCKET")
    generation_provider: str = Field("mock", alias="GENERATION_PROVIDER")
    deepseek_api_key: str = Field("", alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field("https://api.deepseek.com", alias="DEEPSEEK_BASE_URL")
    deepseek_model: str = Field("deepseek-v4-flash", alias="DEEPSEEK_MODEL")
    deepseek_timeout_seconds: int = Field(60, alias="DEEPSEEK_TIMEOUT_SECONDS")
    deepseek_max_tokens: int = Field(10000, alias="DEEPSEEK_MAX_TOKENS")
    max_extracted_chars: int = Field(60000, alias="MAX_EXTRACTED_CHARS")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]

    def runtime_errors(self) -> list[str]:
        errors: list[str] = []
        if not self.supabase_url:
            errors.append("SUPABASE_URL is required")
        if not self.supabase_anon_key:
            errors.append("SUPABASE_ANON_KEY is required")
        if not self.supabase_service_role_key:
            errors.append("SUPABASE_SERVICE_ROLE_KEY is required")
        if self.generation_provider.lower() == "deepseek" and not self.deepseek_api_key:
            errors.append("DEEPSEEK_API_KEY is required when GENERATION_PROVIDER=deepseek")
        if not self.cors_origins:
            errors.append("API_CORS_ORIGINS must contain at least one origin")
        return errors


@lru_cache
def get_settings() -> Settings:
    return Settings()
