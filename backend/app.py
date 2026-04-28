from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import google.generativeai as genai
import os

# ✅ Initialize Flask app FIRST
app = Flask(__name__)
CORS(app)

# 🔑 Google API Key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set!")
genai.configure(api_key=GEMINI_API_KEY)

# ✅ Working model
model = genai.GenerativeModel("models/gemini-flash-latest")

# 🗄️ MongoDB Connection (FIXED FORMAT)
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://ridhiraheja:ridhi24@cluster0.xtijuvx.mongodb.net/")
client_db = MongoClient(MONGO_URI)
db = client_db["chatbot"]
collection = db["history"]

# 🔹 FACT CHECK API
@app.route("/fact-check", methods=["POST"])
def fact_check():
    try:
        data = request.json
        statement = data.get("statement", "")
        email = data.get("email", "anonymous")

        prompt = f"""
You are an AI fact-checker.

Give output in this format:
Verdict: True / False / Uncertain
Confidence: (percentage)
Justification: 2-3 lines explanation

Follow-ups:
1. [First related question to explore further]
2. [Second related question to explore further]

Statement: {statement}
"""

        response = model.generate_content(prompt)
        result = response.text

        # 💾 Save to MongoDB
        collection.insert_one({
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
    query = {"email": email} if email else {}
    chats = list(collection.find(query, {"_id": 0}))
    return jsonify(chats)

# 🚀 Run server
if __name__ == "__main__":
    app.run(debug=True)