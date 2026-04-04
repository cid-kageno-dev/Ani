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
    user_input = request.json.get('message')

    if not user_input:
        return jsonify({"error": "Message is required"}), 400

    print(f"User asking: {user_input}")

    ai_response = get_gemini_response(user_input)

    if ai_response:
        thread = threading.Thread(
            target=save_interaction,
            args=(user_input, ai_response, "AI Response")
        )
        thread.start()

        return jsonify({
            "response": ai_response,
            "source": "AI Response"
        })

    else:
        print("Gemini unavailable, switching to fallback...")
        fallback_msg = get_fallback_answer(user_input)

        thread = threading.Thread(
            target=save_interaction,
            args=(user_input, fallback_msg, "Database")
        )
        thread.start()

        return jsonify({
            "response": fallback_msg,
            "source": "Database"
        })

@main.route('/history', methods=['GET'])
@cross_origin()
def history():
    """Return recent chat interactions from the database."""
    limit = request.args.get('limit', 20, type=int)
    rows = get_recent_interactions(limit=limit)
    interactions = [
        {
            "id": row["id"],
            "user_query": row["user_query"],
            "ai_response": row["ai_response"],
            "source": row["source"],
            "created_at": row["created_at"].isoformat()
        }
        for row in rows
    ]
    return jsonify(interactions)
