from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import google.generativeai as genai

# ✅ Initialize Flask app FIRST
app = Flask(__name__)
CORS(app)

# 🔑 Google API Key
genai.configure(api_key="AIzaSyCcMxRo7TalGgzhlBI746gUYVZmFbpKTNE")

# ✅ Working model
model = genai.GenerativeModel("models/gemini-flash-latest")

# 🗄️ MongoDB Connection (FIXED FORMAT)
client_db = MongoClient("mongodb+srv://ridhiraheja:ridhi24@cluster0.xtijuvx.mongodb.net/")
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