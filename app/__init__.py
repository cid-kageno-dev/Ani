import os
from flask import Flask
from flask_cors import CORS
from app.logger import get_logger, divider, log_box, log_status
from app.services.db_service import ensure_schema
from app.services.firebase_validator import validate_firebase_on_startup

log = get_logger("ani.boot")


def _check_connections():
    from config import Config
    from app.services.db_service import _backend, _get_pool, _get_firestore, _firebase_configured

    results = {}

    # Gemini
    results["gemini"] = (bool(Config.GOOGLE_API_KEYS), Config.GEMINI_MODEL)

    # Firebase
    if _firebase_configured():
        try:
            _get_firestore()
            results["firebase"] = (True, f"collection '{Config.FIREBASE_COLLECTION}'")
        except Exception as e:
            results["firebase"] = (False, str(e)[:50])
    else:
        results["firebase"] = (False, "not configured")

    # PostgreSQL
    if Config.DATABASE_URL:
        try:
            _get_pool()
            results["postgres"] = (True, Config.DATABASE_URL.split("@")[-1].split("?")[0])
        except Exception as e:
            results["postgres"] = (False, str(e)[:50])
    else:
        results["postgres"] = (False, "DATABASE_URL not set")

    # Active DB backend
    results["backend"] = _backend() or "none"

    return results


def create_app() -> Flask:
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates"))
    app = Flask(__name__, template_folder=template_dir)
    CORS(app)

    log_box([
        "  Ani — AI Assistant",
        "  Shadow-Garden.inc",
        "",
        "  Booting up...",
    ])

    # Validate Firebase configuration across environments
    firebase_validation = validate_firebase_on_startup()

    schema_ok = ensure_schema()
    conns     = _check_connections()

    divider()
    print("  CONNECTION STATUS", flush=True)
    divider()
    log_status("Gemini AI",   conns["gemini"][0],   conns["gemini"][1])
    log_status("Firebase",    conns["firebase"][0],  conns["firebase"][1])
    log_status("PostgreSQL",  conns["postgres"][0],  conns["postgres"][1])
    log_status("DB Schema",   schema_ok,             f"active backend: {conns['backend']}")
    divider()

    from app.routes import main
    app.register_blueprint(main)
    log.info("Routes ready  →  / | /api/chat | /api/history | /api/stats | /api/health")
    divider()

    return app
