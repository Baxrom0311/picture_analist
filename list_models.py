import os
import sys
from google import genai
from dotenv import load_dotenv

# Load env variables
load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("Error: GEMINI_API_KEY not found in environment.")
    sys.exit(1)

try:
    client = genai.Client(api_key=api_key)
    print("Fetching available models...")
    
    # List models
    # Note: The new SDK might handle listing differently or via HTTP. 
    # Attempting standard list_models if available, or error handling.
    try:
        # Pager object
        pager = client.models.list() 
        print(f"{'Model Name':<40} | {'Display Name':<40}")
        print("-" * 85)
        
        count = 0
        for model in pager:
            print(f"{model.name:<40} | {model.display_name:<40}")
            count += 1
            if count >= 20: break # limit output
            
    except Exception as e:
        print(f"Error listing models: {e}")

except Exception as e:
    print(f"Client error: {e}")
