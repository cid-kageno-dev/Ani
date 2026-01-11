from flask import Flask, render_template, request, jsonify
# Import your existing AI function
from Ai_service import get_gemini_response 

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    if not user_input:
        return jsonify({"response": "Please say something!"})
    
    # Call your AI Service
    ai_reply = get_gemini_response(user_input)
    
    return jsonify({"response": ai_reply})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
  
