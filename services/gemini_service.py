import google.generativeai as genai
import os
from dotenv import load_dotenv

class GeminiService:
    @staticmethod
    def configure():
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-1.5-flash')

    @staticmethod
    def generate_content(model, prompt):
        return model.generate_content(prompt)
