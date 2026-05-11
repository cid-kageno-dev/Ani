import os
from flask import Flask
from flask_cors import CORS

from app.logger import get_logger, divider, log_box, log_status
from app.services.db_service import ensure_schema, ensure_render_schema

log = get_logger("ani.boot")


def _check_connections() -> dict:
    from config import Config
    from app.services.db_service import (
        _backend,
        _firebase_configured,
        _get_firestore,
        _get_pool,
        _get_render_pool,
    )

    results: dict = {}

    # Gemini
    results["gemini"] = (bool(Config.GOOGLE_API_KEYS), Config.GEMINI_MODEL)

    # Firebase
    if _firebase_configured():
        try:
            _get_firestore()
            results["firebase"] = (True, f"collection '{Config.FIREBASE_COLLECTION}'")
        except Exception as e:
            results["firebase"] = (False, str(e)[:60])
    else:
        results["firebase"] = (False, "not configured")

    # Primary PostgreSQL
    if Config.DATABASE_URL:
        try:
            _get_pool()
            results["postgres"] = (True, Config.DATABASE_URL.split("@")[-1].split("?")[0])
        except Exception as e:
            results["postgres"] = (False, str(e)[:60])
    else:
        results["postgres"] = (False, "DATABASE_URL not set")

    # Render PostgreSQL
    if Config.RENDER_DATABASE_URL:
        try:
            _get_render_pool()
            results["render"] = (True, Config.RENDER_DATABASE_URL.split("@")[-1].split("?")[0])
        except Exception as e:
            results["render"] = (False, str(e)[:60])
    else:
        results["render"] = (False, "RENDER_DATABASE_URL not set")

    results["backend"] = _backend() or "none"
    return results


def create_app() -> Flask:
    template_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "templates")
    )
    app = Flask(__name__, template_folder=template_dir)
    CORS(app)

    log_box([
        "  Ani — AI Assistant",
        "  Shadow-Garden.inc",
        "",
        "  Booting up…",
    ])

    primary_schema_ok = ensure_schema()
    render_schema_ok  = ensure_render_schema()
    conns             = _check_connections()

    divider()
    print("  CONNECTION STATUS", flush=True)
    divider()
    log_status("Gemini AI",         conns["gemini"][0],   conns["gemini"][1])
    log_status("Firebase",          conns["firebase"][0], conns["firebase"][1])
    log_status("PostgreSQL",        conns["postgres"][0], conns["postgres"][1])
    log_status("Render PostgreSQL", conns["render"][0],   conns["render"][1])
    log_status(
        "DB Schema",
        primary_schema_ok or render_schema_ok,
        f"primary={'ok' if primary_schema_ok else 'skip'} | "
        f"render={'ok' if render_schema_ok else 'skip'} | "
        f"active: {conns['backend']}",
    )
    divider()

    from app.routes import main as routes_blueprint
    app.register_blueprint(routes_blueprint)

    log.info("Routes ready  →  / | /chat | /chat/stream | /history | /stats | /health")
    divider()

    return app
