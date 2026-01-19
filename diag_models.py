import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)

models_to_try = [
    'gemini-1.5-flash',
    'gemini-1.5-pro',
    'gemini-pro',
    'gemini-1.0-pro'
]

for model_name in models_to_try:
    print(f"Testing model: {model_name}")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hello")
        print(f"  SUCCESS: {model_name}")
        break  # STOP at first success
    except Exception as e:
        print(f"  FAILED: {model_name} - {type(e).__name__}: {e}")

print("\nListing all supported models again (more carefully):")
try:
    for m in genai.list_models():
        print(f"- {m.name} ({m.supported_generation_methods})")
except Exception as e:
    print(f"Error listing: {e}")
