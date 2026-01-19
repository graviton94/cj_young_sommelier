import os
from dotenv import load_dotenv

print(f"Current Working Directory: {os.getcwd()}")
print(f"Checking for .env file: {os.path.exists('.env')}")

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
if api_key:
    print(f"GEMINI_API_KEY found: {api_key[:5]}...{api_key[-5:]}")
else:
    print("GEMINI_API_KEY NOT found in environment")

# Test if it's available in os.environ
print(f"Keys in os.environ: {[k for k in os.environ.keys() if 'GEMINI' in k]}")
