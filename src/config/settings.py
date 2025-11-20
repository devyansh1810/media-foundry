"""Application settings with Pydantic validation"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration with validation"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    # Server Configuration
    ws_host: str = Field(default="0.0.0.0", description="WebSocket server host")
    ws_port: int = Field(default=8080, ge=1, le=65535, description="WebSocket server port")
    health_port: int = Field(default=8081, ge=1, le=65535, description="Health check port")

    # FFmpeg Configuration
    max_concurrent_jobs: int = Field(
        default=4, ge=1, le=32, description="Maximum concurrent FFmpeg jobs"
    )
    ffmpeg_timeout_seconds: int = Field(
        default=600, ge=10, le=3600, description="FFmpeg process timeout in seconds"
    )
    ffmpeg_threads: int = Field(default=0, ge=0, description="FFmpeg thread count (0=auto)")

    # File Management
    temp_dir: Path = Field(default=Path("/tmp/ffmpeg-jobs"), description="Temporary files directory")
    max_file_size_mb: int = Field(
        default=500, ge=1, le=5000, description="Maximum input file size in MB"
    )
    cleanup_interval_seconds: int = Field(
        default=60, ge=10, le=3600, description="Cleanup interval in seconds"
    )

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )

    # WebSocket Configuration
    ws_max_size: int = Field(
        default=524_288_000, ge=1024, description="Max WebSocket message size in bytes"
    )
    ws_ping_interval: int = Field(
        default=30, ge=5, le=300, description="WebSocket ping interval in seconds"
    )
    ws_ping_timeout: int = Field(
        default=10, ge=5, le=60, description="WebSocket ping timeout in seconds"
    )

    # RabbitMQ Configuration (optional)
    rabbitmq_url: str = Field(
        default="amqp://guest:guest@localhost/",
        description="RabbitMQ connection URL"
    )

    @field_validator("temp_dir")
    @classmethod
    def validate_temp_dir(cls, v: Path) -> Path:
        """Ensure temp directory exists"""
        v.mkdir(parents=True, exist_ok=True)
        return v

    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes"""
        return self.max_file_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
