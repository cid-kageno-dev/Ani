import os
from flask import Flask
from flask_cors import CORS
from app.logger import get_logger
from app.services.db_service import ensure_schema

log = get_logger("ani.boot")

def create_app() -> Flask:
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates"))
    app = Flask(__name__, template_folder=template_dir)
    CORS(app)

    log.info("=" * 52)
    log.info("  Ani — AI Assistant  |  Shadow-Garden.inc")
    log.info("=" * 52)

    ensure_schema()

    from app.routes import main
    app.register_blueprint(main)
    log.info("Routes registered: / /chat /history /stats /health")

    return app
