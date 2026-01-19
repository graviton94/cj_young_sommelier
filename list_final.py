import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)

print("--- MODEL LIST ---")
try:
    for m in genai.list_models():
        print(f"ID: {m.name}")
except Exception as e:
    print(f"Error: {e}")
