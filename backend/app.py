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
if GEMINI_API_KEY and "expired" not in GEMINI_API_KEY.lower():
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        HAS_VALID_KEY = True
    except Exception:
        HAS_VALID_KEY = False

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
        raise ValueError("No valid API key")
    return model.generate_content(prompt)

def get_mock_response(statement):
    # Simple logic to provide a realistic mock response
    verdicts = ["True", "False", "Uncertain"]
    import random
    verdict = random.choice(verdicts)
    confidence = random.randint(70, 99)
    
    return f"""Verdict: {verdict}
Confidence: {confidence}%
Justification: This is a simulated response because the Gemini API key is currently expired or invalid. In a production environment, this would be verified against real-time data.
"""

# 🔹 FACT CHECK API
@app.route("/fact-check", methods=["POST"])
def fact_check():
    try:
        data = request.json
        statement = data.get("statement", "")
        email = data.get("email", "anonymous")
        print(f"Received request from {email}: {statement}")

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
            if HAS_VALID_KEY:
                response = generate_with_retry(prompt)
                result = response.text
            else:
                result = get_mock_response(statement)
        except Exception as e:
            print(f"AI Generation failed: {e}. Using mock.")
            result = get_mock_response(statement)

        # 💾 Save to history
        save_to_history({
            "email": email,
            "statement": statement,
            "response": result
        })

        return jsonify({"result": result})

    except Exception as e:
        return jsonify({"error": str(e)})

# 🔹 HISTORY API
@app.route("/history", methods=["GET"])
def history():
    email = request.args.get("email")
    chats = get_history(email)
    return jsonify(chats)

# 🚀 Run server
if __name__ == "__main__":
    app.run(debug=True, port=5000)
