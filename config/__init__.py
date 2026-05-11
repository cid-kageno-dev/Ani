import os
from app.logger import get_logger, setup_logging

setup_logging(os.getenv("LOG_LEVEL", "DEBUG"))

_log = get_logger("ani.config")


class Config:
    # ── Identity — fill these to personalise the assistant ────────────────
    ASSISTANT_NAME: str    = os.getenv("ASSISTANT_NAME", "Ani")
    OWNER_NAME: str        = os.getenv("OWNER_NAME", "Your Name")
    ORG_NAME: str          = os.getenv("ORG_NAME", "")
    OWNER_EMAIL: str       = os.getenv("OWNER_EMAIL", "")
    OWNER_WEBSITE: str     = os.getenv("OWNER_WEBSITE", "")
    OWNER_FACEBOOK: str    = os.getenv("OWNER_FACEBOOK", "")
    OWNER_TAGLINE: str     = os.getenv(
        "OWNER_TAGLINE",
        "A fast, smart portfolio assistant — live GitHub context, AI responses, and cached fallback knowledge.",
    )
    OWNER_FOOTER_NOTE: str = os.getenv(
        "OWNER_FOOTER_NOTE",
        "Designed for recruiters, collaborators, and anyone curious about the work.",
    )
    CHAT_SUGGESTIONS: list[str] = [
        s.strip()
        for s in os.getenv(
            "CHAT_SUGGESTIONS",
            "What projects have you built?,What's your tech stack?,How can I contact you?,Show your recent GitHub work",
        ).split(",")
        if s.strip()
    ]

    # ── Gemini ────────────────────────────────────────────────────────────
    GOOGLE_API_KEYS: list[str] = [
        v
        for v in (os.getenv(f"GOOGLE_API_KEY{i}") for i in range(1, 20))
        if v
    ]
    if not GOOGLE_API_KEYS:
        _fallback = os.getenv("GOOGLE_API_KEY", "")
        if _fallback:
            GOOGLE_API_KEYS.append(_fallback)

    GEMINI_MODEL: str      = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    GEMINI_TEMP: float     = float(os.getenv("GEMINI_TEMP", "0.55"))
    GEMINI_MAX_TOKENS: int = int(os.getenv("GEMINI_MAX_TOKENS", "512"))

    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_BACKEND: str    = os.getenv("DATABASE_BACKEND", "auto")
    DATABASE_URL: str        = os.getenv("DATABASE_URL", "")
    RENDER_DATABASE_URL: str = os.getenv("RENDER_DATABASE_URL", "")

    # ── Firebase ──────────────────────────────────────────────────────────
    _fb_key_file = "firebase-key.json"
    FIREBASE_CREDENTIALS: str = (
        os.getenv("FIREBASE_CREDENTIALS", "")
        or (_fb_key_file if os.path.isfile(_fb_key_file) else "")
    )
    FIREBASE_SERVICE_ACCOUNT_JSON: str = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "")
    FIREBASE_DATABASE_URL: str         = os.getenv("FIREBASE_DATABASE_URL", "")
    FIREBASE_PROJECT_ID: str           = os.getenv("FIREBASE_PROJECT_ID", "")
    FIREBASE_COLLECTION: str           = os.getenv("FIREBASE_COLLECTION", "chat_interactions")

    # ── GitHub ────────────────────────────────────────────────────────────
    GITHUB_USERNAME: str  = os.getenv("GITHUB_USERNAME", "")
    GITHUB_CACHE_TTL: int = int(os.getenv("GITHUB_CACHE_TTL", "300"))

    # ── App ───────────────────────────────────────────────────────────────
    DEBUG: bool             = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    MAX_MESSAGE_LENGTH: int = int(os.getenv("MAX_MESSAGE_LENGTH", "1200"))


# ── Startup config dump ───────────────────────────────────────────────────
_log.debug("━━━━━━━━━━ CONFIG DUMP ━━━━━━━━━━")
_log.debug(f"  LOG_LEVEL            = {os.getenv('LOG_LEVEL', 'DEBUG')}")
_log.debug(f"  ASSISTANT_NAME       = {Config.ASSISTANT_NAME}")
_log.debug(f"  OWNER_NAME           = {Config.OWNER_NAME}")
_log.debug(f"  ORG_NAME             = {Config.ORG_NAME or '(not set)'}")
_log.debug(f"  OWNER_EMAIL          = {Config.OWNER_EMAIL or '(not set)'}")
_log.debug(f"  OWNER_WEBSITE        = {Config.OWNER_WEBSITE or '(not set)'}")
_log.debug(f"  OWNER_FACEBOOK       = {Config.OWNER_FACEBOOK or '(not set)'}")
_log.debug(f"  GITHUB_USERNAME      = {Config.GITHUB_USERNAME or '(not set)'}")
_log.debug(f"  GITHUB_CACHE_TTL     = {Config.GITHUB_CACHE_TTL}s")
_log.debug(f"  GEMINI_MODEL         = {Config.GEMINI_MODEL}")
_log.debug(f"  GEMINI_TEMP          = {Config.GEMINI_TEMP}")
_log.debug(f"  GEMINI_MAX_TOKENS    = {Config.GEMINI_MAX_TOKENS}")
_log.debug(f"  DATABASE_BACKEND     = {Config.DATABASE_BACKEND}")
_log.debug(f"  DATABASE_URL         = {'set (' + Config.DATABASE_URL.split('@')[-1].split('?')[0] + ')' if Config.DATABASE_URL else 'not set'}")
_log.debug(f"  RENDER_DATABASE_URL  = {'set (' + Config.RENDER_DATABASE_URL.split('@')[-1].split('?')[0] + ')' if Config.RENDER_DATABASE_URL else 'not set'}")
_log.debug(f"  FIREBASE_PROJECT_ID  = {Config.FIREBASE_PROJECT_ID or 'not set'}")
_log.debug(f"  FIREBASE_COLLECTION  = {Config.FIREBASE_COLLECTION}")
_log.debug(f"  MAX_MESSAGE_LENGTH   = {Config.MAX_MESSAGE_LENGTH}")
_log.debug(f"  CHAT_SUGGESTIONS     = {Config.CHAT_SUGGESTIONS}")
_log.debug("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

_firebase_set = (
    Config.FIREBASE_CREDENTIALS
    or Config.FIREBASE_SERVICE_ACCOUNT_JSON
    or Config.FIREBASE_PROJECT_ID
)

if Config.GOOGLE_API_KEYS:
    _log.info(f"Loaded {len(Config.GOOGLE_API_KEYS)} Gemini API key(s)")
else:
    _log.warning("No Gemini API keys found — AI responses will be unavailable")

_log.info(f"Identity: {Config.ASSISTANT_NAME} / {Config.OWNER_NAME}" + (f" / {Config.ORG_NAME}" if Config.ORG_NAME else ""))
_log.info(f"Database backend: {Config.DATABASE_BACKEND}")

if _firebase_set:
    _log.info(f"Firebase configured — collection '{Config.FIREBASE_COLLECTION}'")
else:
    _log.warning("Firebase not configured")

if Config.DATABASE_URL:
    _log.info("DATABASE_URL is set")
else:
    _log.warning("DATABASE_URL not set")

if Config.RENDER_DATABASE_URL:
    _log.info("RENDER_DATABASE_URL is set")

if not (Config.DATABASE_URL or _firebase_set):
    _log.warning("No database backend configured — database features will be unavailable")

if not Config.GITHUB_USERNAME:
    _log.warning("GITHUB_USERNAME not set — GitHub context will be unavailable")
