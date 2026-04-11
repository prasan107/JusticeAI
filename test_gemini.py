# save as test_gemini.py in your justiceai/ root folder and run it
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# List all models available to YOUR key
for m in genai.list_models():
    if "generateContent" in m.supported_generation_methods:
        print(m.name)