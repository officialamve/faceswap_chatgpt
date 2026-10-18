from dataclasses import dataclass
import os
from pathlib import Path

class ConfigError(ValueError):
    pass

def _int_env(name: str, default: int, minimum: int = 1) -> int:
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc
    if value < minimum:
        raise ConfigError(f"{name} must be >= {minimum}")
    return value

@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_id: int
    port: int
    webhook_url: str
    webhook_secret: str
    processing_timeout: int
    download_timeout: int
    max_input_bytes: int
    max_image_pixels: int
    max_image_dimension: int
    temp_dir: Path
    log_level: str
    source_face_model: str
    swap_model: str

    @classmethod
    def from_env(cls):
        token = os.getenv("BOT_TOKEN", "").strip()
        if not token or ":" not in token:
            raise ConfigError("BOT_TOKEN is missing or malformed")
        raw_admin = os.getenv("ADMIN_TELEGRAM_ID", "").strip()
        try:
            admin = int(raw_admin)
            if admin <= 0: raise ValueError
        except ValueError as exc:
            raise ConfigError("ADMIN_TELEGRAM_ID must be a positive numeric Telegram ID") from exc
        webhook_url = os.getenv("WEBHOOK_URL", "").strip().rstrip("/")
        secret = os.getenv("WEBHOOK_SECRET", "").strip()
        if not webhook_url.startswith("https://"):
            raise ConfigError("WEBHOOK_URL must be an https:// URL for webhook deployment")
        if len(secret) < 32 or not secret.replace("_", "").replace("-", "").isalnum():
            raise ConfigError("WEBHOOK_SECRET must be at least 32 URL-safe characters")
        return cls(token, admin, _int_env("PORT", 10000), webhook_url, secret,
                   _int_env("PROCESSING_TIMEOUT_SECONDS", 600), _int_env("DOWNLOAD_TIMEOUT_SECONDS", 60),
                   _int_env("MAX_INPUT_BYTES", 15 * 1024 * 1024), _int_env("MAX_IMAGE_PIXELS", 20_000_000),
                   _int_env("MAX_IMAGE_DIMENSION", 8000), Path(os.getenv("TEMP_DIR", "/tmp/face-swap-bot")),
                   os.getenv("LOG_LEVEL", "INFO").upper(), os.getenv("SOURCE_FACE_MODEL", "models/face_analysis"),
                   os.getenv("SWAP_MODEL", "models/inswapper_128.onnx"))
