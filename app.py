import os
from dotenv import load_dotenv
import google.generativeai as genai
# Import 'send_from_directory'
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
# The API key is now loaded from the .env file
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file or environment variables.")
    genai.configure(api_key=api_key)
    
    # FIX 1: Updated model name to the one you were using before
    model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025') 

except (KeyError, ValueError) as e:
    print("="*50)
    print(f"ERROR: {e}")
    print("Please create a .env file in the same directory as this script")
    print("and add your API key like this: GOOGLE_API_KEY='your-api-key-here'")
    print("="*50)
    exit()


# --- NEW: This is the "Face" for your bot ---
@app.route('/')
def serve_chat_page():
    """
    Serves the 'bot.html' file when someone visits the main URL.
    """
    # This tells Flask to find 'bot.html' in the same folder and send it.
    return send_from_directory('.', 'bot.html')


# --- NEW: Chat Endpoint ---
@app.route('/api/chat', methods=['POST'])
# ... (rest of your chat() function is perfect) ...
    try:
        # The chat-bison model is optimized for multi-turn conversations
        chat_session = model.start_chat(history=history)
        # Get the last user message from the history
        last_user_message = history[-1]['parts'][0]['text']
        
        response = chat_session.send_message(last_user_message)
        return jsonify({'status': 'success', 'message': response.text})

    except Exception as e:
        print(f"An error occurred during chat: {e}")
        return jsonify({'error': 'Failed to get a response from the AI model.'}), 500


# --- Automation Action Placeholders ---
def send_email(recipient, subject, body):
    """Placeholder function to send an email."""
    print("--- SIMULATING EMAIL ---")
    print(f"To: {recipient}")
    print(f"Subject: {subject}")
    print(f"Body: {body}")
    print("-------------------------")
    return f"Successfully sent an email to {recipient} with the subject '{subject}'."

def schedule_meeting(title, date, time, attendees):
    """Placeholder function to schedule a meeting."""
    print("--- SIMULATING MEETING SCHEDULING ---")
    print(f"Title: {title}")
    print(f"Date: {date}")
    print(f"Time: {time}")
    print(f"Attendees: {', '.join(attendees)}")
    print("-----------------------------------")
    return f"Successfully scheduled a meeting '{title}' on {date} at {time}."


# --- Automation Endpoint ---
@app.route('/api/automate', methods=['POST'])
def automate_task():
# ... (rest of your automate_task() function is perfect) ...
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

    - For 'send_email', extract 'recipient', 'subject', and 'body'. The recipient should be a valid email address.
    - For 'schedule_meeting', extract 'title', 'date', 'time', and 'attendees' (as a list of strings).

    If the command is ambiguous, lacks necessary information, or doesn't match a known action, set the action to 'unknown' and provide a helpful 'error_message'.

    Respond ONLY with a valid JSON object.

    Example Command: "send an email to jane@example.com about the project update. The body should be 'Hi Jane, please see the attached report.'"
    Example JSON:
    {
      "action": "send_email",
      "parameters": {
        "recipient": "jane@example.com",
        "subject": "Project Update",
        "body": "Hi Jane, please see the attached report."
      }
    }
    """
    
    prompt = f"User Command: \"{user_command}\""

    try:
        # FIX 2: Updated GenerationConfig to the modern syntax
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
                 return jsonify({'status': 'error', 'message': "I'm missing some details. I need a recipient, subject, and body to send an email."})

        elif action == 'schedule_meeting':
            if all(k in params for k in ['title', 'date', 'time', 'attendees']):
                result_message = schedule_meeting(params['title'], params['date'], params['time'], params['attendees'])
                return jsonify({'status': 'success', 'message': result_message})
            else:
                return jsonify({'status': 'error', 'message': "I'm missing some details. To schedule a meeting I need a title, date, time, and at least one attendee."})
        
        else:
            error_msg = task_data.get('error_message', "I'm sorry, I don't understand that command or I'm missing the necessary information to complete it.")
            return jsonify({'status': 'error', 'message': error_msg})

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'error': 'Failed to process command with AI model.'}), 500

# This is used for local testing. Gunicorn will ignore it.
if __name__ == '__main__':
    # Render will provide its own port, so 5000 is just for local testing
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)), host='0.0.0.0')
