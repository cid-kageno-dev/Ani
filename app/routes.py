from flask import Blueprint, request, jsonify
from flask_cors import cross_origin  # <--- 1. Import cross_origin
from app.services.ai_service import get_gemini_response
from app.services.sheet_service import save_interaction_background, get_fallback_answer
import threading

main = Blueprint('main', __name__)

@main.route('/chat', methods=['POST'])
@cross_origin() # <--- 2. Add this decorator to fix the CORS error
def chat():
    user_input = request.json.get('message')
    
    if not user_input:
        return jsonify({"error": "Message is required"}), 400

    print(f"User asking: {user_input}")

    # 1. Try Gemini AI
    ai_response = get_gemini_response(user_input)

    if ai_response:
        # SUCCESS:
        # Start a background thread to save to sheet (Non-blocking)
        thread = threading.Thread(
            target=save_interaction_background, 
            args=(user_input, ai_response)
        )
        thread.start()

        return jsonify({
            "response": ai_response,
            "source": "AI Response"
        })

    else:
        # FAILURE:
        # AI failed, check Google Sheet for similar past answer
        print("Gemini unavailable, switching to fallback...")
        fallback_msg = get_fallback_answer(user_input)
        
        return jsonify({
            "response": fallback_msg,
            "source": "Database"
        })
        
