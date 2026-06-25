"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# .env nằm cùng cấp với thư mục src/ (project root). Dùng đường dẫn tuyệt đối
# để bot có thể chạy từ bất kỳ CWD nào, không phụ thuộc working directory.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Cấu hình chính của bot, đọc từ .env / biến môi trường."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Telegram
    telegram_bot_token: str = Field(..., description="Token từ @BotFather")

    # OpenAI / OpenAI-compatible (DeepSeek, OpenRouter, custom proxy...)
    openai_api_key: str = Field(..., description="API key của provider")
    openai_model: str = Field(
        default="mimo-v2.5-free",
        description="Model dùng để dịch (vd: gpt-4o-mini, deepseek-v4-flash-free)",
    )
    openai_base_url: str | None = Field(
        default=None,
        description=(
            "Base URL cho OpenAI-compatible endpoint. "
            "Để None dùng OpenAI chính thức, hoặc set sang DeepSeek/OpenRouter/proxy."
        ),
    )
    openai_timeout_seconds: float = Field(
        default=60.0, description="Timeout khi gọi API (giây)"
    )
    openai_max_retries: int = Field(
        default=0,
        description=(
            "Số lần retry tự động của OpenAI SDK khi gặp lỗi. "
            "Mặc định SDK = 2, nhưng với cold start 60-80s thì 3 lần × 60s + backoff "
            "≈ 200s — quá lâu. Set 0 để fail-fast khi timeout."
        ),
    )
    enable_thinking: bool = Field(
        default=False,
        description=(
            "Bật/tắt chế độ thinking của model (pass qua extra_body). "
            "Một số model (GLM-4.7, Qwen3, ...) mặc định bật thinking → dễ rate limit."
        ),
    )

    # Bot behavior
    default_target_lang: str = Field(
        default="vi", description="Ngôn ngữ đích mặc định (ISO 639-1)"
    )
    max_text_length: int = Field(
        default=4000, description="Giới hạn ký tự mỗi tin nhắn"
    )

    # Rate limiting
    rate_limit_max_requests: int = Field(
        default=10,
        description="Số request tối đa mỗi user trong window (rate_limit_window_seconds)",
    )
    rate_limit_window_seconds: int = Field(
        default=60,
        description="Khoảng thời gian (giây) để reset rate limit counter",
    )

    # Webhook (cho production deployment trên Render)
    webhook_enabled: bool = Field(
        default=False,
        description="Bật webhook thay vì polling (cho Render/cloud)",
    )
    webhook_url: str | None = Field(
        default=None,
        description=(
            "Public URL của bot (vd: https://tele-bot-dich.onrender.com). "
            "Để None → dùng RENDER_EXTERNAL_URL (Render tự set)."
        ),
    )
    webhook_port: int = Field(
        default=8443,
        description="Port cho webhook server (Render override bằng PORT env)",
    )
    webhook_path: str = Field(
        default="/webhook",
        description="Path cho webhook endpoint (vd: /webhook)",
    )
    webhook_secret_token: str | None = Field(
        default=None,
        description="Secret token xác thực webhook (tự do đặt, Telegram dùng để verify)",
    )

    # Logging
    log_level: str = Field(default="INFO", description="Mức log")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Trả về singleton Settings (cache để không đọc .env nhiều lần)."""
    return Settings()  # type: ignore[call-arg]


# Biến toàn cục để import nhanh: `from tele_bot_dich.config import settings`
settings = get_settings()
