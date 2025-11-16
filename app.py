import os
from flask import Flask, request, jsonify

# --- IMPORTANT ---
# Import the main function from your agent.py file
# I'm guessing your function is named 'get_ai_response'
# Change this line to match your project:
from agent import get_ai_response 
# ---

# Create the Flask web app
app = Flask(__name__)

# This is the (hidden) health check route that Render uses
@app.route('/')
def hello_world():
    return 'Aiva is running!'

# This is the main endpoint your chatbot will use
@app.route('/chat', methods=['POST'])
def chat():
    try:
        # Get the user's message from the incoming JSON request
        data = request.json
        user_message = data.get('message')

        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        # --- Call your AI agent ---
        # This calls the function you imported from agent.py
        ai_response = get_ai_response(user_message) 
        # ---

        # Send the AI's response back as JSON
        return jsonify({"reply": ai_response})

    except Exception as e:
        print(f"An error occurred in /chat: {e}")
        return jsonify({"error": "Internal server error"}), 500

# This is the code that Render will actually run
if __name__ == "__main__":
    # Get the port from the environment variable (set by Render)
    # Default to 10000 for local testing if no port is set
    port = int(os.environ.get('PORT', 10000))
    
    # Run the app, listening on all network interfaces
    # '0.0.0.0' is required for Render
    app.run(host='0.0.0.0', port=port)