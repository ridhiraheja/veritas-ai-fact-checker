from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()
# ✅ Initialize Flask app FIRST
app = Flask(__name__)
CORS(app)

# 🔑 Google API Key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
HAS_VALID_KEY = False
model = None

# Using a stable flash model for high quota
STABLE_MODEL_NAME = "gemini-flash-latest"

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(STABLE_MODEL_NAME)
        HAS_VALID_KEY = True
        print(f"Initialized Gemini model: {STABLE_MODEL_NAME}")
    except Exception as e:
        print(f"Error initializing Gemini model: {e}")
        HAS_VALID_KEY = False
else:
    print("Warning: GEMINI_API_KEY not found in environment.")

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
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def generate_with_retry(prompt):
    if not HAS_VALID_KEY:
        raise ValueError("No valid API key configured.")
    return model.generate_content(prompt)

# 🔹 HEALTH API
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "online",
        "db": "connected" if db_available else "fallback",
        "api": "configured" if HAS_VALID_KEY else "missing"
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
                return jsonify({
                    "error": "Fact-checking service is not configured (API key missing or invalid).",
                    "status": "error"
                }), 503

            response = generate_with_retry(prompt)
            result = response.text
        except Exception as e:
            error_msg = str(e)
            print(f"AI Generation failed: {error_msg}")
            
            # Categorize the error for the user
            friendly_error = "Fact-checking service unavailable"
            if "quota" in error_msg.lower() or "429" in error_msg:
                friendly_error = "API quota exceeded. Please wait a moment and try again."
            elif "key" in error_msg.lower() or "401" in error_msg:
                friendly_error = "Invalid API key configuration."
            
            return jsonify({
                "error": friendly_error,
                "details": error_msg,
                "status": "error"
            }), 500

        # 💾 Save to history
        from datetime import datetime
        save_to_history({
            "email": email,
            "statement": statement,
            "response": result,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
    app.run(debug=True, port=5000)
