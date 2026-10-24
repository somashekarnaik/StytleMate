from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    database_url: str = f"sqlite:///{(PROJECT_ROOT / 'stylemate.db').as_posix()}"
    upload_dir: str = "storage/clothing"
    max_upload_bytes: int = 8 * 1024 * 1024
    frontend_origin: str = "http://localhost:5173"
    ollama_host: str = "http://127.0.0.1:11434"
    ollama_vision_model: str = "qwen2.5vl:3b"
    ollama_timeout_seconds: int = 120

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        return path if path.is_absolute() else PROJECT_ROOT / path


settings = Settings()
