import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    
    models_to_test = [
        "gemini-3-flash-preview", 
        "gemini-flash-latest", 
        "gemini-flash-lite-latest",
        "gemini-2.5-flash-lite"
    ]
    
    for m_name in models_to_test:
        print(f"Testing {m_name}...")
        try:
            model = genai.GenerativeModel(m_name)
            response = model.generate_content("Ping")
            print(f"  SUCCESS: {response.text.strip()}")
        except Exception as e:
            print(f"  FAILED: {e}")
else:
    print("No API key")
