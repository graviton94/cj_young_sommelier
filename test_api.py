from src.llm import GeminiFlavorReporter
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

import google.generativeai as genai
try:
    reporter = GeminiFlavorReporter(api_key=api_key)
    print("Testing compound prediction with gemini-pro...")
    
    # DEBUG: List models visible to this reporter
    print("Models visible to this API Key:")
    for m in genai.list_models():
         print(f"  - {m.name}")

    preds = reporter.predict_compound_info(
        name="Ethyl vinyl ether",
        cas="109-92-2",
        mw=72.11,
        log_p=1.17,
        groups="Ether, Alkene",
        baseline_threshold=0.0
    )
    print(f"Predictions: {preds}")
except Exception as e:
    print(f"Gemini API Error: {e}")
    import traceback
    traceback.print_exc()
