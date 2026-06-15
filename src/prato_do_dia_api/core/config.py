from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Prato do Dia API"
    app_env: str = "development"
    database_url: str = "sqlite:///./data/prato_do_dia.db"
    max_upload_bytes: int = 5 * 1024 * 1024
    max_image_width: int = 4096
    max_image_height: int = 4096
    public_assets_base_path: str = "/v1/assets"
    ml_root: str | None = None
    ml_models_dir: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
