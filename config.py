import os
import json
from app.logger import get_logger, setup_logging

setup_logging(os.getenv("LOG_LEVEL", "INFO"))

log = get_logger("ani.config")

_FIREBASE_SERVICE_ACCOUNT = {
    "type": "service_account",
    "project_id": "gen-lang-client-0109922552",
    "private_key_id": "f86a6d93961c7653582b2ebe2506006cd4a8f9db",
    "private_key": (
        "-----BEGIN PRIVATE KEY-----\n"
        "MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDSntqzdHR4G/SJ\n"
        "gevzR/5oooS8ePAiXnz6Gafk9scN1yjLYygoCqhe/Q3zfXYhDz/t71rECSyfIn67\n"
        "609j8VNR01goWTElm9zbjcNlMOEKkM9n71n8PYFT4L/jTg1vK7rYiny0WNF/Fbd+\n"
        "k15P5AQyodZdaA+/gU1iZrgHRtJrMdPjNWTMDVVfV1DI/eiqRylLZiXU6qeacgX9\n"
        "kZB8Jym/QlnnJ3jfLloqg+ldMI12h3uULsQ3fOQZlcJqX3u7Cg2lB3gImCr24+aW\n"
        "5IVl0ZH27g3U2vkd8W4E0KvlOYmsrOi5jbw6ZNiwyYN/wBM4IfXbBB/ILo05iYB/\n"
        "ar6qFuS5AgMBAAECggEAI/n7fHzPajbIOfbF0XwCMmhUSQdVaWF/co8QVTVsAeq3\n"
        "Lqqk0NYlNXh/OhC7rWD3+BITDHpOs24GfN3wZS9zHn59yAKYOQbbHmukLTRAtHfQ\n"
        "3b2OPt5YqXWyAUczV0J+e3+IVpv3SQByI/5TNU1LBEUNo03jpsAU8lJ+a8vGpIWC\n"
        "fvCH6BaaWS3TiVUaCOZR2XcQELvWKniEDiI6XcXfDBKVDu4w0dwHgZKml9pZqacx\n"
        "SZqf3ooo3Ior6Y+BieYhq/0GrOJSFTc0fgpgMDGF9Q2n2gyH7fILtjKDvpx07CtS\n"
        "9GI6l14A4UK12lhSHPPN28hOY1zgAr2sjq36i/aY6QKBgQDwNorb9cYlCRJ6XhU2\n"
        "5wAYH6MvMq3Vmy4PAwj0E7iX9+25AD3+Ikcrnrf3oU8oSPamIYYoj0VSrTD8LsyU\n"
        "XBq0Uq5fqDLfApir61HzS/flkMzYNuskTLgpfaHhoE4I5Ni1eR2rLdmXxVlRvyZQ\n"
        "MU5vp0VkrAHjnzmejd5gnw0OpQKBgQDgdm7lttV3Qb2T4OI8sxcSdNzCHBgM3V7S\n"
        "tLuebohHEaZbaolkas8draZSbsfxPyej/+sn1iLXE29XM5JgJBFgHF/HzUiWEeED\n"
        "I+LVXeD85NRRE8HjpeCUnnUlX7p+z58S+syjanNlbzcW5GWoPdaJJnF9M5Xts7+2\n"
        "qyLBi3PVhQKBgQDYwU7BtuAKUUpkMvtPpFhYbEvy7fcgdbu0/hcZL6Z1MtpHAqnt\n"
        "5P51pO36PIvSHSy7sip99PIn7XHzTUN7aDUMnEMOvBbTV2NuVpSHRvi1JNlDDSNX\n"
        "iQbxIZVupBlmOyI1dsnHykK7ie/ULPkkialuZPDgK7o0rFvw77FHXJ4KpQKBgQDH\n"
        "+Hsf590RW94bKpQjY6HAbaBmxkSe4XEi4qTrpql+Nzkv5B/2+DkAxb2RXuR+Bre4\n"
        "Ib1MRjfPyJ6+31EemcNpDp4+EKMEH3WJKKVjVTml0+9bM/DecN89SFYxL7GkXC/p\n"
        "5sn9JE8eJRC9Mklms4C3uyoMUrLVi/fWM2zJZQWTSQKBgGUTFL5ClzJQl6qW0dUg\n"
        "bk+gb6vDg1txxHFu3KVviM5akAp5Qb3E7ZJvw/86syfVR3DsD4akPoVnTsO4qfTm\n"
        "rXDlMqyMVPXScRwg4DA0xM6tdB7gDRX/hR87+oPW/XHk3ssODnPy/GVkJGOINvKg\n"
        "COMR5SnrQ1Q3xL/4mFSISTuq\n"
        "-----END PRIVATE KEY-----\n"
    ),
    "client_email": "firebase-adminsdk-fbsvc@gen-lang-client-0109922552.iam.gserviceaccount.com",
    "client_id": "110977084371482518677",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40gen-lang-client-0109922552.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com",
}


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

    DATABASE_BACKEND: str = "firebase"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    FIREBASE_CREDENTIALS: str = "firebase-key.json"
    FIREBASE_SERVICE_ACCOUNT_JSON: str = json.dumps(_FIREBASE_SERVICE_ACCOUNT)
    FIREBASE_DATABASE_URL: str = "https://gen-lang-client-0109922552-default-rtdb.asia-southeast1.firebasedatabase.app"
    FIREBASE_PROJECT_ID: str = "gen-lang-client-0109922552"
    FIREBASE_COLLECTION: str = "chat_interactions"

    GITHUB_USERNAME: str = "cid-kageno-dev"
    GITHUB_CACHE_TTL: int = int(os.getenv("GITHUB_CACHE_TTL", "300"))

    GEMINI_MODEL: str    = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    GEMINI_TEMP: float   = float(os.getenv("GEMINI_TEMP", "0.55"))
    GEMINI_MAX_TOKENS: int = int(os.getenv("GEMINI_MAX_TOKENS", "512"))

    DEBUG: bool = os.getenv("FLASK_DEBUG", "true").lower() == "true"

    if GOOGLE_API_KEYS:
        log.info(f"Loaded {len(GOOGLE_API_KEYS)} Gemini API key(s)")
    else:
        log.warning("No Gemini API keys found — AI responses will be unavailable")

    log.info(f"Database backend: {DATABASE_BACKEND}")
    log.info(f"Firebase configured — project '{FIREBASE_PROJECT_ID}', collection '{FIREBASE_COLLECTION}'")

    if DATABASE_URL:
        log.info("DATABASE_URL is set (PostgreSQL fallback available)")
    else:
        log.warning("DATABASE_URL not set")
