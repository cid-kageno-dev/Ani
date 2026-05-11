import os
from app.logger import get_logger, setup_logging

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

    DATABASE_BACKEND: str = os.getenv("DATABASE_BACKEND", "auto")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    RENDER_DATABASE_URL: str = os.getenv("RENDER_DATABASE_URL", "")

    _fb_creds_env = os.getenv("FIREBASE_CREDENTIALS", "")
    _fb_key_file  = "firebase-key.json"
    FIREBASE_CREDENTIALS: str = (
        _fb_creds_env if _fb_creds_env
        else _fb_key_file if os.path.isfile(_fb_key_file)
        else ""
    )
    FIREBASE_SERVICE_ACCOUNT_JSON: str = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "")
    FIREBASE_DATABASE_URL: str = os.getenv("FIREBASE_DATABASE_URL", "")
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "")
    FIREBASE_COLLECTION: str = os.getenv("FIREBASE_COLLECTION", "chat_interactions")

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

    log.info(f"Database backend preference: {DATABASE_BACKEND}")

    if FIREBASE_CREDENTIALS or FIREBASE_SERVICE_ACCOUNT_JSON or FIREBASE_PROJECT_ID:
        log.info(f"Firebase configured — collection '{FIREBASE_COLLECTION}'")
    else:
        log.warning("Firebase not configured")

    if DATABASE_URL:
        log.info("DATABASE_URL is set")
    else:
        log.warning("DATABASE_URL not set")

    if not (DATABASE_URL or FIREBASE_CREDENTIALS or FIREBASE_SERVICE_ACCOUNT_JSON or FIREBASE_PROJECT_ID):
        log.warning("No database backend configured — database features will be unavailable")
