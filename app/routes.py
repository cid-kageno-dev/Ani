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
from app.logger import get_logger, divider
import threading

log      = get_logger("ani.routes")
log_chat = get_logger("ani.chat")
main     = Blueprint("main", __name__)


def _bg(fn, *args):
    threading.Thread(target=fn, args=args, daemon=True).start()


def _log_message(user_input: str, response: str, source: str, ms: float):
    divider()
    log_chat.info(f"USER  ▶  {user_input}")
    divider("·")
    log_chat.info(f"ANI   ◀  [{source}] ({ms:.0f}ms)")
    for line in response.splitlines():
        print(f"          {line}", flush=True)
    divider()


@main.route("/")
def home():
    log.info("Serving chat UI")
    return render_template("index.html")


@main.route("/api/chat", methods=["POST"])
@cross_origin()
def chat():
    t0         = time.perf_counter()
    data       = request.get_json(silent=True) or {}
    user_input = data.get("message", "").strip()

    if not user_input:
        log.warning("Empty message received — rejected")
        return jsonify({"error": "Message is required"}), 400

    ai_response = get_gemini_response(user_input)
    ms          = (time.perf_counter() - t0) * 1000

    if ai_response:
        _bg(save_interaction, user_input, ai_response, "AI Response")
        _log_message(user_input, ai_response, "AI Response", ms)
        return jsonify({"response": ai_response, "source": "AI Response"})

    log.warning(f"Gemini unavailable after {ms:.0f}ms — using fallback")
    fallback = get_fallback_answer(user_input)
    _bg(save_interaction, user_input, fallback, "Database")
    ms2 = (time.perf_counter() - t0) * 1000
    _log_message(user_input, fallback, "Database Fallback", ms2)
    return jsonify({"response": fallback, "source": "Database"})


@main.route("/api/history", methods=["GET"])
@cross_origin()
def history():
    requested_limit = request.args.get("limit", 20, type=int) or 20
    limit = max(1, min(requested_limit, 100))
    log.debug(f"GET /api/history  limit={limit}")
    rows = get_recent_interactions(limit=limit)
    return jsonify([
        {
            "id":          row["id"],
            "user_query":  row["user_query"],
            "ai_response": row["ai_response"],
            "source":      row["source"],
            "created_at":  row["created_at"].isoformat(),
        }
        for row in rows
    ])


@main.route("/api/stats", methods=["GET"])
@cross_origin()
def stats():
    log.debug("GET /api/stats")
    data = get_stats()
    log.debug(
        f"Stats  →  total={data.get('total', 0)} | "
        f"ai={data.get('ai_responses', 0)} | "
        f"fallback={data.get('fallback_responses', 0)}"
    )
    return jsonify(data)


@main.route("/api/health", methods=["GET"])
def health():
    log.debug("GET /api/health  →  ok")
    return jsonify({"status": "ok"})
