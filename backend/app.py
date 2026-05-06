from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import google.generativeai as genai
import os
import json
from datetime import datetime, timezone
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

load_dotenv()
# ✅ Initialize Flask app FIRST
app = Flask(__name__)
CORS(app)

# Using a stable flash model for high quota
STABLE_MODEL_NAME = "models/gemini-2.5-flash-lite"
HAS_VALID_KEY = False
model = None

def init_gemini():
    global model, HAS_VALID_KEY, STABLE_MODEL_NAME
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        key = key.strip().strip("'\"")
        try:
            genai.configure(api_key=key)
            
            # Dynamically find an available flash model
            try:
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                print(f"Available models: {available_models}")
                
                # Priority list for selection (high quota / high availability lite models first)
                for preferred in ["models/gemini-2.5-flash-lite", "models/gemini-flash-lite-latest", "models/gemini-2.0-flash", "models/gemini-flash-latest", "models/gemini-3-flash-preview", "models/gemini-pro"]:
                    if preferred in available_models:
                        STABLE_MODEL_NAME = preferred
                        break
                else:
                    if available_models:
                        STABLE_MODEL_NAME = available_models[0]
            except Exception as list_err:
                print(f"Warning: could not list models dynamically ({list_err}). Using default STABLE_MODEL_NAME.")
                STABLE_MODEL_NAME = "models/gemini-2.5-flash-lite"
            
            model = genai.GenerativeModel(STABLE_MODEL_NAME)
            HAS_VALID_KEY = True
            print(f"Dynamically selected Gemini model: {STABLE_MODEL_NAME}")
            return True
        except Exception as e:
            print(f"Error initializing Gemini model: {e}")
            err_msg = str(e).lower()
            if any(x in err_msg for x in ["key", "401", "unauthorized", "api_key"]):
                HAS_VALID_KEY = False
            else:
                # If it's a transient rate limit or network issue, the key itself is still configured
                HAS_VALID_KEY = True
                STABLE_MODEL_NAME = "models/gemini-2.5-flash-lite"
                model = genai.GenerativeModel(STABLE_MODEL_NAME)
    else:
        HAS_VALID_KEY = False
    return HAS_VALID_KEY

init_gemini()

# 🗄️ MongoDB Connection
MONGO_URI = os.environ.get("MONGO_URI")
db_available = False
collection = None

try:
    if MONGO_URI:
        client_db = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        # Force a connection check
        client_db.admin.command('ping')
        db = client_db["chatbot"]
        collection = db["history"]
        db_available = True
        print("Connected to MongoDB Atlas")
except Exception as e:
    print(f"MongoDB not available, using local mock storage: {e}")
    db_available = False

# Local mock storage if DB fails
LOCAL_HISTORY_FILE = "chat_history.json"

def save_to_history(data):
    if db_available and collection is not None:
        try:
            collection.insert_one(data.copy())
            return
        except Exception:
            pass
    
    # Fallback to local file
    history = []
    if os.path.exists(LOCAL_HISTORY_FILE):
        try:
            with open(LOCAL_HISTORY_FILE, "r") as f:
                history = json.load(f)
        except:
            history = []
    
    history.append(data)
    with open(LOCAL_HISTORY_FILE, "w") as f:
        json.dump(history, f)

def get_history(email):
    if db_available and collection is not None:
        try:
            query = {"email": email} if email else {}
            return list(collection.find(query, {"_id": 0}))
        except Exception:
            pass
    
    # Fallback to local file
    if os.path.exists(LOCAL_HISTORY_FILE):
        try:
            with open(LOCAL_HISTORY_FILE, "r") as f:
                history = json.load(f)
                if email:
                    return [c for c in history if c.get("email") == email]
                return history
        except:
            return []
    return []

@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    reraise=True
)
def generate_with_retry(prompt):
    if not HAS_VALID_KEY or model is None:
        raise ValueError("No valid API key configured.")
    return model.generate_content(prompt)

def generate_with_fallback(prompt):
    global STABLE_MODEL_NAME, model
    
    # Try the currently selected stable model first
    try:
        print(f"Attempting generation with primary model: {STABLE_MODEL_NAME}")
        return generate_with_retry(prompt)
    except Exception as e:
        err_msg = str(e)
        print(f"Primary model {STABLE_MODEL_NAME} failed: {err_msg}")
        
        # If it's an authorization/authentication issue, do not attempt fallback models
        lower_err = err_msg.lower()
        if any(x in lower_err for x in ["key", "401", "unauthorized", "api_key"]) and "no valid api key configured" not in lower_err:
            raise e
            
        # Try fallback models in priority order (high availability lite models first)
        fallbacks = [
            "models/gemini-2.5-flash-lite",
            "models/gemini-flash-lite-latest",
            "models/gemini-2.0-flash",
            "models/gemini-2.5-flash",
            "models/gemini-flash-latest",
            "models/gemini-3-flash-preview",
            "models/gemini-1.5-flash",
            "models/gemini-pro"
        ]
        
        # Remove the current STABLE_MODEL_NAME from fallbacks to avoid repeating
        if STABLE_MODEL_NAME in fallbacks:
            fallbacks.remove(STABLE_MODEL_NAME)
            
        for fallback_model_name in fallbacks:
            print(f"Attempting fallback generation with model: {fallback_model_name}")
            try:
                fallback_model = genai.GenerativeModel(fallback_model_name)
                response = fallback_model.generate_content(prompt)
                
                # Promote fallback model to primary so future requests are fast
                STABLE_MODEL_NAME = fallback_model_name
                model = fallback_model
                print(f"Successfully switched and promoted to fallback model: {STABLE_MODEL_NAME}")
                return response
            except Exception as fe:
                print(f"Fallback model {fallback_model_name} failed: {fe}")
                
        # If all fallbacks failed, raise the original exception
        raise e

# 🔹 HEALTH API
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "online",
        "db": "connected" if db_available else "fallback",
        "api": "configured" if HAS_VALID_KEY else "missing",
        "version": "2.1-dynamic-fix"
    })

# 🔹 FACT CHECK API
@app.route("/fact-check", methods=["POST"])
def fact_check():
    try:
        data = request.json
        statement = data.get("statement", "")
        email = data.get("email", "anonymous")
        print(f"Received request from {email}: {statement}")

        if not statement.strip():
            return jsonify({"error": "Please provide a statement to check."}), 400

        prompt = f"""
You are an AI fact-checker.

Give output in this format:
Verdict: True / False / Uncertain
Confidence: (percentage)
Justification: 2-3 lines explanation

Statement: {statement}

IMPORTANT: Provide ONLY the requested format. Do NOT include any follow-up questions, suggestions, or additional information.
"""

        try:
            if not HAS_VALID_KEY or model is None:
                # Try to re-init in case env var was added after startup
                if not init_gemini():
                    return jsonify({
                        "error": "Fact-checking service is not configured (API key missing or invalid).",
                        "status": "error"
                    }), 503

            print(f"Attempting generation with {STABLE_MODEL_NAME}...")
            try:
                response = generate_with_fallback(prompt)
                result = response.text
            except Exception as e:
                raise e
        except Exception as e:
            error_msg = str(e)
            print(f"AI Generation failed: {error_msg}")
            
            # Categorize the error for the user
            friendly_error = "Fact-checking service unavailable"
            lower_msg = error_msg.lower()
            
            if any(x in lower_msg for x in ["quota", "429", "resourceexhausted", "exhausted", "limit"]):
                friendly_error = "API quota exceeded. Please wait a moment or try again later."
            elif "no valid api key configured" in lower_msg:
                friendly_error = "Fact-checking service is not configured (API key missing)."
            elif any(x in lower_msg for x in ["401", "unauthorized"]):
                friendly_error = "Invalid API key configuration."
            elif any(x in lower_msg for x in ["notfound", "not found", "model", "404"]):
                friendly_error = f"AI model ({STABLE_MODEL_NAME}) not found. Raw error: {error_msg}"
            
            return jsonify({
                "error": friendly_error,
                "details": error_msg,
                "status": "error"
            }), 500

        # 💾 Save to history
        save_to_history({
            "email": email,
            "statement": statement,
            "response": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        return jsonify({"result": result})

    except Exception as e:
        print(f"Unhandled error: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

# 🔹 HISTORY API
@app.route("/history", methods=["GET"])
def history():
    email = request.args.get("email")
    chats = get_history(email)
    return jsonify(chats)

@app.route("/clear-history", methods=["POST"])
def clear_history():
    try:
        data = request.json
        email = data.get("email", "anonymous")
        
        if db_available and collection is not None:
            query = {"email": email} if email else {}
            collection.delete_many(query)
        
        # Also clear local file if it exists
        if os.path.exists(LOCAL_HISTORY_FILE):
            if email and email != "anonymous":
                try:
                    with open(LOCAL_HISTORY_FILE, "r") as f:
                        history = json.load(f)
                    new_history = [c for c in history if c.get("email") != email]
                    with open(LOCAL_HISTORY_FILE, "w") as f:
                        json.dump(new_history, f)
                except:
                    pass
            else:
                os.remove(LOCAL_HISTORY_FILE)
                
        return jsonify({"status": "success", "message": "History cleared"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🚀 Run server
if __name__ == "__main__":
    # Use the port assigned by the cloud provider (Render/Heroku/etc.) or default to 5000
    port = int(os.environ.get("PORT", 5000))
    # host='0.0.0.0' is required for cloud deployment and local network access
    app.run(debug=True, host='0.0.0.0', port=port)
