from flask import Flask, render_template, request, jsonify
import os
import sys
import requests
import vertexai
from vertexai.generative_models import GenerativeModel, Content, Part
import logging
import uuid
from threading import Lock
from opentelemetry import trace

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

app = Flask(__name__)

# In-memory session storage
SESSIONS = {}
SESSION_LOCKS = {}
GLOBAL_LOCK = Lock()
MAX_SESSIONS = 5000
MAX_HISTORY_LENGTH = 40 # 20 turns * 2 messages per turn

# Configuration
# vLLM Configuration
VLLM_API_URL = os.environ.get("VLLM_API_URL", "http://localhost:8000/v1/chat/completions")
MODEL_NAME = os.environ.get("MODEL_NAME", "google/gemma-3-medium")

# Gemini Configuration (via Vertex AI)
USE_GEMINI_API = os.environ.get("USE_GEMINI_API", "false").lower() == "true"
VERTEX_PROJECT = os.environ.get("VERTEX_PROJECT")
VERTEX_LOCATION = os.environ.get("VERTEX_LOCATION", "us-central1")
GEMINI_MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME", "gemini-2.5-flash")

# App Version
APP_VERSION = os.environ.get("APP_VERSION", "local")
GPU_TYPE = os.environ.get("GPU_TYPE", "Unknown GPU")
NODE_NAME = os.environ.get("NODE_NAME", "Localhost")

if USE_GEMINI_API:
    vertexai.init(project=VERTEX_PROJECT, location=VERTEX_LOCATION)

@app.route('/')
def index():
    # Clean model name (remove provider prefix like "google/")
    clean_model_name = MODEL_NAME.split('/')[-1] if '/' in MODEL_NAME else MODEL_NAME

    # Display name: show Gemini model when using managed API, otherwise show vLLM model
    if USE_GEMINI_API:
        display_model_name = GEMINI_MODEL_NAME
    else:
        # Convert e.g. "google-gemma-3-4b-it" to "Gemma 3 4B"
        display_model_name = clean_model_name.replace("google-", "").replace("-it", "")
        parts = display_model_name.split("-")
        display_model_name = " ".join(p.upper() if p.endswith("b") else p.capitalize() for p in parts)

    return render_template('index.html', 
                         app_version=APP_VERSION,
                         model_name=clean_model_name,
                         display_model_name=display_model_name,
                         gpu_type=GPU_TYPE,
                         node_name=NODE_NAME)

@app.route('/architecture')
def architecture():
    return render_template('architecture.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message')
    session_id = data.get('session_id')
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Initialize or retrieve session (Thread-Safe)
    session_lock = None
    with GLOBAL_LOCK:
        if not session_id or session_id not in SESSIONS:
            # Enforce Max Sessions Limit
            if len(SESSIONS) >= MAX_SESSIONS:
                # Remove oldest session (Dicts are insertion-ordered in Python 3.7+)
                oldest_key = next(iter(SESSIONS))
                del SESSIONS[oldest_key]
                if oldest_key in SESSION_LOCKS:
                    del SESSION_LOCKS[oldest_key]
                logging.warning(f"Max sessions ({MAX_SESSIONS}) reached. Deleted oldest session: {oldest_key}")

            session_id = str(uuid.uuid4())
            SESSIONS[session_id] = []
            SESSION_LOCKS[session_id] = Lock()
            logging.info(f"Created new session: {session_id}")
        
        session_lock = SESSION_LOCKS[session_id]

    # Acquire per-session lock for history modification
    with session_lock:
        # Enforce Max Turns Limit (Reset if exceeded)
        if len(SESSIONS[session_id]) >= MAX_HISTORY_LENGTH:
            SESSIONS[session_id] = []
            logging.info(f"Session {session_id} reached max turns limit. History cleared.")

        # Update history with user message
        history = SESSIONS[session_id]
        
        # Prevent consecutive user messages (e.g. from race conditions or retries)
        if history and history[-1].get("role") == "user":
            logging.warning(f"Session {session_id} has consecutive user messages. Removing previous incomplete turn.")
            history.pop()

        history.append({"role": "user", "content": user_message})
        
        # Create a snapshot of history for the API call to prevent mutation during network wait
        history_snapshot = list(history)

    # Log Request
    logging.info(f"Session {session_id} - Request: {user_message}")
    
    # Get current span
    span = trace.get_current_span()
    if span:
        span.set_attribute("genai.request.body", user_message)
        span.set_attribute("genai.model", MODEL_NAME)
        span.set_attribute("session.id", session_id)

    try:
        bot_response = ""
        prompt_tokens = 0
        completion_tokens = 0
        
        if USE_GEMINI_API:
            # Vertex AI Gemini (ChatSession via Workload Identity / ADC)
            model = GenerativeModel(GEMINI_MODEL_NAME)
            
            # Convert internal history to Vertex AI format (excluding the last user message which is sent in send_message)
            gemini_history = []
            for msg in history_snapshot[:-1]:
                role = "user" if msg["role"] == "user" else "model"
                gemini_history.append(Content(role=role, parts=[Part.from_text(msg["content"])]))
            
            chat_session = model.start_chat(history=gemini_history)
            response = chat_session.send_message(user_message)
            bot_response = response.text
            
            # Extract usage metadata if available
            if response.usage_metadata:
                prompt_tokens = response.usage_metadata.prompt_token_count
                completion_tokens = response.usage_metadata.candidates_token_count
            
        else:
            # Proxy request to vLLM (Stateless API, requires full history)
            payload = {
                "model": MODEL_NAME,
                "messages": history_snapshot, # Send immutable snapshot
                "max_tokens": data.get('max_tokens', 64),
                "temperature": data.get('temperature', 0.7),
                "stream": False
            }
            response = requests.post(VLLM_API_URL, json=payload)
            response.raise_for_status()
            data = response.json()
            bot_response = data['choices'][0]['message']['content']
            
            # Extract usage metadata
            usage = data.get('usage', {})
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)

        # Log Response (Truncated) & Token Usage
        truncated_response = bot_response
        if len(bot_response) > 80:
            truncated_response = f"{bot_response[:40]}...{bot_response[-40:]}"
            
        logging.info(f"Session {session_id} - Response: {truncated_response} | Usage: Prompt Tokens={prompt_tokens}, Completion Tokens={completion_tokens}")
        
        # Update history with bot response (Acquire Lock Again)
        with session_lock:
            # Verify we are still adding to the same conversation state
            SESSIONS[session_id].append({"role": "assistant", "content": bot_response})

        if span:
            span.set_attribute("genai.response.body", bot_response)
            
        return jsonify({
            "response": bot_response,
            "session_id": session_id
        })

    except Exception as e:
        # Log the full error to the console/stderr so it's visible in logs
        logging.error(f"Error processing chat request for session {session_id}: {e}")
        
        # Roll back history on failure to prevent role alternation errors (user, user)
        with session_lock:
            if session_id in SESSIONS and len(SESSIONS[session_id]) > 0:
                last_msg = SESSIONS[session_id][-1]
                if last_msg.get("role") == "user":
                    SESSIONS[session_id].pop()
                    logging.info(f"Rolled back last user message for session {session_id} due to error.")

        if span:
            span.record_exception(e)
            span.set_attribute("error.message", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
            
