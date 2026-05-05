import time
from flask import Blueprint, request, jsonify, render_template
from flask_cors import cross_origin
from app.services.ai_service import get_gemini_response
from app.services.db_service import (
    save_interaction,
    get_fallback_answer,
    get_recent_interactions,
    get_stats,
)
from app.logger import get_logger
import threading

log = get_logger("ani.routes")
main = Blueprint("main", __name__)

def _bg(fn, *args):
    threading.Thread(target=fn, args=args, daemon=True).start()

@main.route("/")
def home():
    log.info("Serving chat UI")
    return render_template("index.html")

@main.route("/chat", methods=["POST"])
@cross_origin()
def chat():
    t0   = time.perf_counter()
    data = request.get_json(silent=True) or {}
    user_input = data.get("message", "").strip()

    if not user_input:
        log.warning("Empty message received")
        return jsonify({"error": "Message is required"}), 400

    log.info(f"POST /chat — '{user_input[:80]}'")

    ai_response = get_gemini_response(user_input)
    ms = (time.perf_counter() - t0) * 1000

    if ai_response:
        _bg(save_interaction, user_input, ai_response, "AI Response")
        log.info(f"Response sent [AI] in {ms:.0f}ms")
        return jsonify({"response": ai_response, "source": "AI Response"})

    log.warning(f"AI unavailable after {ms:.0f}ms — engaging fallback")
    fallback = get_fallback_answer(user_input)
    _bg(save_interaction, user_input, fallback, "Database")
    ms2 = (time.perf_counter() - t0) * 1000
    log.info(f"Response sent [Fallback] in {ms2:.0f}ms total")
    return jsonify({"response": fallback, "source": "Database"})

@main.route("/history", methods=["GET"])
@cross_origin()
def history():
    requested_limit = request.args.get("limit", 20, type=int) or 20
    limit = max(1, min(requested_limit, 100))
    log.info(f"GET /history?limit={limit}")
    rows = get_recent_interactions(limit=limit)
    return jsonify([
        {
            "id":         row["id"],
            "user_query": row["user_query"],
            "ai_response":row["ai_response"],
            "source":     row["source"],
            "created_at": row["created_at"].isoformat(),
        }
        for row in rows
    ])

@main.route("/stats", methods=["GET"])
@cross_origin()
def stats():
    log.info("GET /stats")
    return jsonify(get_stats())

@main.route("/health", methods=["GET"])
def health():
    log.debug("GET /health")
    return jsonify({"status": "ok"})
