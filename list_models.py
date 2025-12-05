import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load your .env file where GOOGLE_API_KEY is stored
load_dotenv()

# Set up Gemini client
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# List and print available models
models = genai.list_models()

print("\nAvailable Models:\n")
for model in models:
    print(f"{model.name} -> {model.supported_generation_methods}")
