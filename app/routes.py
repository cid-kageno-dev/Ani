from flask import Blueprint, request, jsonify, render_template
from flask_cors import cross_origin
from app.services.ai_service import get_gemini_response
from app.services.db_service import save_interaction, get_fallback_answer, get_recent_interactions
import threading

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('index.html')

@main.route('/chat', methods=['POST'])
@cross_origin()
def chat():
    data = request.get_json(silent=True)
    user_input = (data or {}).get('message', '').strip()

    if not user_input:
        return jsonify({"error": "Message is required"}), 400

    print(f"[Chat] {user_input[:80]}")

    ai_response = get_gemini_response(user_input)

    if ai_response:
        threading.Thread(
            target=save_interaction,
            args=(user_input, ai_response, "AI Response"),
            daemon=True
        ).start()
        return jsonify({"response": ai_response, "source": "AI Response"})

    fallback = get_fallback_answer(user_input)
    threading.Thread(
        target=save_interaction,
        args=(user_input, fallback, "Database"),
        daemon=True
    ).start()
    return jsonify({"response": fallback, "source": "Database"})

@main.route('/history', methods=['GET'])
@cross_origin()
def history():
    limit = min(request.args.get('limit', 20, type=int), 100)
    rows = get_recent_interactions(limit=limit)
    return jsonify([
        {
            "id": row["id"],
            "user_query": row["user_query"],
            "ai_response": row["ai_response"],
            "source": row["source"],
            "created_at": row["created_at"].isoformat(),
        }
        for row in rows
    ])
