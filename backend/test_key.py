import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")

print(f"API Key found: {API_KEY[:5]}...{API_KEY[-5:] if API_KEY else ''}")

try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("gemini-3-flash-preview")
    response = model.generate_content("test")
    print("Success! Response received.")
    print(response.text)
except Exception as e:
    print(f"Error: {e}")
