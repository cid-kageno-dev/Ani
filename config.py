import os
from dotenv import load_dotenv
from app.logger import get_logger, setup_logging

load_dotenv()
setup_logging(os.getenv("LOG_LEVEL", "INFO"))

log = get_logger("ani.config")

class Config:
    GOOGLE_API_KEYS: list[str] = []

    _i = 1
    while True:
        _key = os.getenv(f"GOOGLE_API_KEY{_i}")
        if not _key:
            break
        GOOGLE_API_KEYS.append(_key)
        _i += 1

    if not GOOGLE_API_KEYS:
        _single = os.getenv("GOOGLE_API_KEY")
        if _single:
            GOOGLE_API_KEYS.append(_single)

    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    GITHUB_USERNAME: str = os.getenv("GITHUB_USERNAME", "cid-kageno-dev")
    GITHUB_CACHE_TTL: int = int(os.getenv("GITHUB_CACHE_TTL", "300"))

    GEMINI_MODEL: str    = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    GEMINI_TEMP: float   = float(os.getenv("GEMINI_TEMP", "0.55"))
    GEMINI_MAX_TOKENS: int = int(os.getenv("GEMINI_MAX_TOKENS", "512"))

    DEBUG: bool = os.getenv("FLASK_DEBUG", "true").lower() == "true"

    if GOOGLE_API_KEYS:
        log.info(f"Loaded {len(GOOGLE_API_KEYS)} Gemini API key(s)")
    else:
        log.warning("No Gemini API keys found — AI responses will be unavailable")

    if DATABASE_URL:
        log.info("DATABASE_URL is set")
    else:
        log.warning("DATABASE_URL not set — database features will be unavailable")
