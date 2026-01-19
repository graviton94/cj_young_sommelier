from src.llm import GeminiFlavorReporter
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

try:
    reporter = GeminiFlavorReporter(api_key=api_key)
    preds = reporter.predict_compound_info(
        name="Ethyl vinyl ether",
        cas="109-92-2",
        mw=72.11,
        log_p=1.17,
        groups="Ether, Alkene",
        baseline_threshold=0.0123 # Dummy baseline
    )
    print(preds)
except Exception as e:
    print(f"ERROR: {e}")
