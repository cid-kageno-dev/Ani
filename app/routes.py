import json
import threading
import time
from datetime import datetime

from flask import Blueprint, Response, jsonify, render_template, request, stream_with_context
from flask_cors import cross_origin

from app.logger import get_logger, divider
from app.services.ai_service import get_gemini_response, get_gemini_response_stream
from app.services.db_service import (
    get_fallback_answer,
    get_recent_interactions,
    get_stats,
    save_interaction,
)
from config import Config

log      = get_logger("ani.routes")
log_chat = get_logger("ani.chat")
main     = Blueprint("main", __name__)

# ── Helpers ───────────────────────────────────────────────────────────────

def _bg(fn, *args) -> None:
    threading.Thread(target=fn, args=args, daemon=True).start()


def _err(message: str, status: int = 400) -> tuple:
    return jsonify({"error": message, "status": status}), status


def _validate_message(data: dict) -> tuple[str, str | None]:
    """Return (message, error_string). error_string is None on success."""
    raw = data.get("message", "")
    if not isinstance(raw, str):
        return "", "Message must be a string"
    text = raw.strip()
    if not text:
        return "", "Message is required"
    if len(text) > Config.MAX_MESSAGE_LENGTH:
        return "", f"Message exceeds maximum length of {Config.MAX_MESSAGE_LENGTH} characters"
    return text, None


def _log_exchange(user_input: str, response: str, source: str, ms: float) -> None:
    divider()
    log_chat.info(f"USER  ▶  {user_input[:120]}")
    divider("·")
    log_chat.info(f"ANI   ◀  [{source}] ({ms:.0f}ms)")
    for line in response.splitlines():
        print(f"          {line}", flush=True)
    divider()


def _dt_iso(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str):
        return value
    return str(value)


# ── Routes ────────────────────────────────────────────────────────────────

@main.route("/")
def home():
    log.info("Serving chat UI")
    return render_template("index.html")


@main.route("/chat/stream", methods=["POST"])
@cross_origin()
def chat_stream():
    data       = request.get_json(silent=True) or {}
    user_input, err = _validate_message(data)

    if err:
        return _err(err)

    log.info(f"Stream: '{user_input[:80]}{'…' if len(user_input) > 80 else ''}'")
    t0 = time.perf_counter()

    stream = get_gemini_response_stream(user_input)

    if stream is None:
        log.warning("Gemini stream unavailable — using DB fallback")
        fallback = get_fallback_answer(user_input)
        _bg(save_interaction, user_input, fallback, "Database")

        def _fallback_gen():
            yield f"data: {json.dumps({'token': fallback, 'done': False})}\n\n"
            yield f"data: {json.dumps({'done': True, 'source': 'Database'})}\n\n"

        return Response(
            stream_with_context(_fallback_gen()),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    full_text: list[str] = []

    def _generate():
        try:
            for chunk in stream:
                token = chunk.text or ""
                if token:
                    full_text.append(token)
                    yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"

            collected = "".join(full_text)
            ms        = (time.perf_counter() - t0) * 1000
            log.info(f"Stream complete in {ms:.0f}ms — {len(collected)} chars")
            _bg(save_interaction, user_input, collected, "AI Response")
            yield f"data: {json.dumps({'done': True, 'source': 'AI Response'})}\n\n"

        except Exception as e:
            log.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'done': True, 'error': True, 'source': 'Error'})}\n\n"

    return Response(
        stream_with_context(_generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@main.route("/chat", methods=["POST"])
@cross_origin()
def chat():
    t0         = time.perf_counter()
    data       = request.get_json(silent=True) or {}
    user_input, err = _validate_message(data)

    if err:
        log.warning(f"Bad request: {err}")
        return _err(err)

    ai_response = get_gemini_response(user_input)
    ms          = (time.perf_counter() - t0) * 1000

    if ai_response:
        _bg(save_interaction, user_input, ai_response, "AI Response")
        _log_exchange(user_input, ai_response, "AI Response", ms)
        return jsonify({"response": ai_response, "source": "AI Response"})

    log.warning(f"Gemini unavailable after {ms:.0f}ms — using DB fallback")
    fallback = get_fallback_answer(user_input)
    _bg(save_interaction, user_input, fallback, "Database")
    ms2 = (time.perf_counter() - t0) * 1000
    _log_exchange(user_input, fallback, "Database", ms2)
    return jsonify({"response": fallback, "source": "Database"})


@main.route("/history", methods=["GET"])
@cross_origin()
def history():
    requested = request.args.get("limit", 20, type=int)
    limit     = max(1, min(requested, 100))
    log.info(f"GET /history  limit={limit}")

    rows = get_recent_interactions(limit=limit)
    return jsonify([
        {
            "id":          row.get("id"),
            "user_query":  row.get("user_query", ""),
            "ai_response": row.get("ai_response", ""),
            "source":      row.get("source", ""),
            "created_at":  _dt_iso(row.get("created_at")),
        }
        for row in rows
    ])


@main.route("/stats", methods=["GET"])
@cross_origin()
def stats():
    log.info("GET /stats")
    data = get_stats()
    log.info(
        f"Stats → total={data.get('total', 0)} | "
        f"ai={data.get('ai_responses', 0)} | "
        f"fallback={data.get('fallback_responses', 0)}"
    )
    return jsonify(data)


@main.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "ani"}), 200


@main.app_errorhandler(404)
def not_found(_):
    return _err("Resource not found", 404)


@main.app_errorhandler(405)
def method_not_allowed(_):
    return _err("Method not allowed", 405)


@main.app_errorhandler(500)
def internal_error(e):
    log.error(f"Unhandled server error: {e}")
    return _err("Internal server error", 500)
