import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
print(f"Key found: {bool(GEMINI_API_KEY)}")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    
    # Try multiple model names to see what works
    models_to_try = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro", "gemini-3-flash-preview"]
    
    for model_name in models_to_try:
        print(f"\nTrying model: {model_name}")
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Test message: Hello!")
            print(f"SUCCESS with {model_name}: {response.text.strip()}")
            break
        except Exception as e:
            print(f"FAILED with {model_name}: {e}")
else:
    print("No API key found in .env")
