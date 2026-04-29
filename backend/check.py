import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set!")

genai.configure(api_key=API_KEY)

for m in genai.list_models():
    print(m.name)