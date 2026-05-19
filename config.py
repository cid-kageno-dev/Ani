import os
import json
from pathlib import Path
from app.logger import get_logger, setup_logging

setup_logging(os.getenv("LOG_LEVEL", "INFO"))

log = get_logger("ani.config")


def load_config(config_path: str = "config.json") -> dict:
    """Load configuration from config.json file."""
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        log.error(f"Configuration file not found: {config_path}")
        log.info("Please copy config.example.json to config.json and update values")
        raise
    except json.JSONDecodeError as e:
        log.error(f"Invalid JSON in config file: {e}")
        raise


# Load configuration from config.json
_CONFIG = load_config()


class Config:
    """Application configuration loaded from config.json and environment variables."""

    # App Info (from config.json)
    APP_NAME: str = _CONFIG.get("app", {}).get("name", "Ani")
    APP_VERSION: str = _CONFIG.get("app", {}).get("version", "1.0.0")
    APP_DESCRIPTION: str = _CONFIG.get("app", {}).get("description", "")
    APP_AUTHOR: str = _CONFIG.get("app", {}).get("author", "")

    # Server (from config.json)
    SERVER_HOST: str = _CONFIG.get("server", {}).get("host", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("PORT", _CONFIG.get("server", {}).get("port", 5000)))
    SERVER_THREADED: bool = _CONFIG.get("server", {}).get("threaded", True)

    # Database (from config.json)
    DATABASE_BACKEND: str = _CONFIG.get("database", {}).get("backend", "firebase")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # Firebase (from environment variables only — never hardcoded)
    FIREBASE_CREDENTIALS: str = ""
    FIREBASE_SERVICE_ACCOUNT_JSON: str = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "")
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", _CONFIG.get("database", {}).get("firebase", {}).get("project_id", ""))
    FIREBASE_DATABASE_URL: str = os.getenv("FIREBASE_DATABASE_URL", _CONFIG.get("database", {}).get("firebase", {}).get("database_url", ""))
    FIREBASE_COLLECTION: str = _CONFIG.get("database", {}).get("firebase", {}).get("collection", "chat_interactions")

    # GitHub (from config.json)
    GITHUB_USERNAME: str = _CONFIG.get("github", {}).get("username", "cid-kageno-dev")
    GITHUB_CACHE_TTL: int = _CONFIG.get("github", {}).get("cache_ttl", 300)

    # Gemini API (from environment variables only - NOT from config.json)
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

    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
    GEMINI_TEMP: float = float(os.getenv("GEMINI_TEMP", "0.2"))
    GEMINI_MAX_TOKENS: int = int(os.getenv("GEMINI_MAX_TOKENS", "4096"))

    # Debug (from config.json or environment)
    DEBUG: bool = _CONFIG.get("app", {}).get("debug", os.getenv("FLASK_DEBUG", "true").lower() == "true")

    # Logging (from config.json or environment)
    LOG_LEVEL: str = _CONFIG.get("logging", {}).get("level", os.getenv("LOG_LEVEL", "INFO"))

    # Features (from config.json)
    FEATURES: dict = _CONFIG.get("features", {})

    # AI system prompt template (from config.json)
    # Use {context} as a placeholder — it is filled at runtime with live GitHub data.
    AI_SYSTEM_PROMPT: str = _CONFIG.get("ai", {}).get("system_prompt", "")

    # Logging initialization
    if GOOGLE_API_KEYS:
        log.info(f"Loaded {len(GOOGLE_API_KEYS)} Gemini API key(s)")
    else:
        log.warning("No Gemini API keys found — AI responses will be unavailable")

    log.info(f"Application: {APP_NAME} v{APP_VERSION}")
    log.info(f"Database backend: {DATABASE_BACKEND}")
    log.info(f"Firebase configured — project '{FIREBASE_PROJECT_ID}', collection '{FIREBASE_COLLECTION}'")
    log.info(f"GitHub username: {GITHUB_USERNAME}")

    if DATABASE_URL:
        log.info("DATABASE_URL is set (PostgreSQL fallback available)")
    else:
        log.warning("DATABASE_URL not set")
