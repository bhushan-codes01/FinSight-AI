import os
import requests
from dotenv import load_dotenv

load_dotenv()

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.endpoint = os.getenv(
            "GEMINI_ENDPOINT",
            "https://gemini.googleapis.com/v1/models/gemini-1.5-gamma:generateMessage",
        )

    def analyze(self, prompt):
        if not self.api_key:
            return "Gemini API key is not configured. Please update the .env file."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "message": {
                "content": [{"type": "text", "text": prompt}],
                "role": "user",
            },
            "temperature": 0.7,
            "maxOutputTokens": 400,
        }

        try:
            response = requests.post(self.endpoint, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            if "candidates" in data and data["candidates"]:
                return data["candidates"][0].get("content", "No response returned from Gemini.")
            if "output" in data and "content" in data["output"]:
                return " ".join(item.get("text", "") for item in data["output"]["content"])
            return data.get("response", "No response returned from Gemini.")
        except requests.RequestException as exc:
            return f"AI service error: {exc}"
