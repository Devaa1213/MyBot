import os
from dotenv import load_dotenv
import google.generativeai as genai
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json

# Load environment variables from .env file
load_dotenv()

# Initialize Flask App
app = Flask(__name__)
# Enable CORS to allow the frontend to communicate with this backend
CORS(app)

# --- AI Configuration ---
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file or environment variables.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025') 
except (KeyError, ValueError) as e:
    print("="*50)
    print(f"ERROR: {e}")
    print("Please create a .env file in the same directory as this script")
    print("and add your API key like this: GOOGLE_API_KEY='your-api-key-here'")
    print("="*50)
    exit()

# --- Serve the HTML Page ---
@app.route('/')
def serve_chat_page():
    """
    Serves the 'bot.html' file when someone visits the main URL.
    """
    return send_from_directory('.', 'bot.html')

# --- Chat Endpoint ---
@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Handles general chat conversations.
    """
    data = request.get_json()
    if not data or 'history' not in data:
        return jsonify({'error': 'No conversation history provided'}), 400

    history = data['history']

    try:
        chat_session = model.start_chat(history=history)
        last_user_message = history[-1]['parts'][0]['text']
        
        response = chat_session.send_message(last_user_message)
        return jsonify({'status': 'success', 'message': response.text})

    except Exception as e:
        print(f"An error occurred during chat: {e}")
        return jsonify({'error': 'Failed to get a response from the AI model.'}), 500

# --- Automation Action Placeholders ---
def send_email(recipient, subject, body):
    """Placeholder function to send an email."""
    print(f"--- SIMULATING EMAIL To: {recipient} ---")
    return f"Successfully sent an email to {recipient} with the subject '{subject}'."

def schedule_meeting(title, date, time, attendees):
    """Placeholder function to schedule a meeting."""
    print(f"--- SIMULATING MEETING: {title} ---")
    return f"Successfully scheduled a meeting '{title}' on {date} at {time}."

# --- Automation Endpoint ---
@app.route('/api/automate', methods=['POST'])
def automate_task():
    """
    This endpoint receives a natural language command, parses it using AI,
    and triggers the corresponding automation task.
    """
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400

    user_command = data['message']

    system_instruction = """
    You are an intelligent assistant that parses natural language commands into structured JSON.
    Analyze the user's command and identify the intended action and its parameters.
    The possible actions are 'send_email', 'schedule_meeting', or 'unknown'.

    - For 'send_email', extract 'recipient', 'subject', and 'body'.
    - For 'schedule_meeting', extract 'title', 'date', 'time', and 'attendees' (as a list).

    If the command is ambiguous, lacks information, or doesn't match a known action, 
    set the action to 'unknown' and provide a helpful 'error_message'.

    Respond ONLY with a valid JSON object.
    """
    
    prompt = f"User Command: \"{user_command}\""

    try:
        generation_config = {
            "response_mime_type": "application/json",
        }
        
        response = model.generate_content(
            [system_instruction, prompt],
            generation_config=generation_config
        )
        
        task_data = json.loads(response.text)
        action = task_data.get('action')
        params = task_data.get('parameters', {})

        if action == 'send_email':
            if all(k in params for k in ['recipient', 'subject', 'body']):
                result_message = send_email(params['recipient'], params['subject'], params['body'])
                return jsonify({'status': 'success', 'message': result_message})
            else:
                 return jsonify({'status': 'error', 'message': "I'm missing details. I need a recipient, subject, and body to send an email."})

        elif action == 'schedule_meeting':
            if all(k in params for k in ['title', 'date', 'time', 'attendees']):
                result_message = schedule_meeting(params['title'], params['date'], params['time'], params['attendees'])
                return jsonify({'status': 'success', 'message': result_message})
            else:
                return jsonify({'status': 'error', 'message': "I'm missing details. I need a title, date, time, and attendees."})
        
        else:
            error_msg = task_data.get('error_message', "I'm sorry, I don't understand that command.")
            return jsonify({'status': 'error', 'message': error_msg})

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'error': 'Failed to process command with AI model.'}), 500

# This is used for local testing. Gunicorn will ignore it.
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, port=port, host='0.0.0.0')
