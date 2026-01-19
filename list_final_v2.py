import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)

with open('models_final.txt', 'w', encoding='utf-8') as f:
    try:
        for m in genai.list_models():
            f.write(f"{m.name}\n")
    except Exception as e:
        f.write(f"Error: {e}")
