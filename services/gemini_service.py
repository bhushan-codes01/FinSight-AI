import os
import requests
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "..", ".env"))

class GeminiService:
    def __init__(self, model_name=None):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not model_name:
            model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.model_name = model_name
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"

    def analyze(self, prompt):
        if not self.api_key or self.api_key.strip() == "" or "your_" in self.api_key.lower():
            return "Gemini API key is not configured or is a placeholder. Please update the .env file with a valid Google AI Studio API key."

        headers = {
            "Content-Type": "application/json",
        }
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 800,
            }
        }

        import time
        max_retries = 2
        backoff = 2.0
        for attempt in range(max_retries + 1):
            try:
                url = f"{self.endpoint}?key={self.api_key}"
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                if response.status_code == 429 and attempt < max_retries:
                    if self.model_name == "gemini-2.5-pro":
                        self.model_name = "gemini-2.5-flash"
                        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
                        url = f"{self.endpoint}?key={self.api_key}"
                        response = requests.post(url, json=payload, headers=headers, timeout=30)
                        if response.status_code != 429:
                            response.raise_for_status()
                            data = response.json()
                            if "candidates" in data and data["candidates"]:
                                candidate = data["candidates"][0]
                                if "content" in candidate and "parts" in candidate["content"]:
                                    parts = candidate["content"]["parts"]
                                    if parts and "text" in parts[0]:
                                        return parts[0]["text"]
                            return "No response returned from Gemini."

                    sleep_time = backoff
                    try:
                        err_json = response.json()
                        details = err_json.get("error", {}).get("details", [])
                        for detail in details:
                            if "retryDelay" in detail:
                                delay_str = detail["retryDelay"]
                                if delay_str.endswith("s"):
                                    sleep_time = float(delay_str[:-1]) + 0.5
                                    break
                    except Exception:
                        pass
                    time.sleep(sleep_time)
                    backoff = max(backoff * 2, sleep_time * 1.5)
                    continue
                response.raise_for_status()
                data = response.json()
                if "candidates" in data and data["candidates"]:
                    candidate = data["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        parts = candidate["content"]["parts"]
                        if parts and "text" in parts[0]:
                            return parts[0]["text"]
                return "No response returned from Gemini."
            except requests.RequestException as exc:
                if attempt == max_retries or (exc.response is not None and exc.response.status_code != 429):
                    return f"AI service error: {exc}"
                time.sleep(backoff)
                backoff *= 2

    def analyze_with_history(self, contents, system_instruction=None, tools=None):
        if not self.api_key or self.api_key.strip() == "" or "your_" in self.api_key.lower():
            return {"text": "Gemini API key is not configured or is a placeholder. Please update the .env file with a valid Google AI Studio API key."}

        headers = {
            "Content-Type": "application/json",
        }
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 800,
            }
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }
        if tools:
            payload["tools"] = tools

        import time
        max_retries = 2
        backoff = 2.0
        for attempt in range(max_retries + 1):
            try:
                url = f"{self.endpoint}?key={self.api_key}"
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                if response.status_code == 429 and attempt < max_retries:
                    if self.model_name == "gemini-2.5-pro":
                        self.model_name = "gemini-2.5-flash"
                        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
                        url = f"{self.endpoint}?key={self.api_key}"
                        response = requests.post(url, json=payload, headers=headers, timeout=30)
                        if response.status_code != 429:
                            response.raise_for_status()
                            data = response.json()
                            if "candidates" in data and data["candidates"]:
                                candidate = data["candidates"][0]
                                if "content" in candidate and "parts" in candidate["content"]:
                                    parts = candidate["content"]["parts"]
                                    if parts:
                                        part = parts[0]
                                        if "functionCall" in part:
                                            return {"functionCall": part["functionCall"]}
                                        if "text" in part:
                                            return {"text": part["text"]}
                            return {"text": "No response returned from Gemini."}

                    sleep_time = backoff
                    try:
                        err_json = response.json()
                        details = err_json.get("error", {}).get("details", [])
                        for detail in details:
                            if "retryDelay" in detail:
                                delay_str = detail["retryDelay"]
                                if delay_str.endswith("s"):
                                    sleep_time = float(delay_str[:-1]) + 0.5
                                    break
                    except Exception:
                        pass
                    time.sleep(sleep_time)
                    backoff = max(backoff * 2, sleep_time * 1.5)
                    continue
                response.raise_for_status()
                data = response.json()
                if "candidates" in data and data["candidates"]:
                    candidate = data["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        parts = candidate["content"]["parts"]
                        if parts:
                            part = parts[0]
                            if "functionCall" in part:
                                return {"functionCall": part["functionCall"]}
                            if "text" in part:
                                return {"text": part["text"]}
                return {"text": "No response returned from Gemini."}
            except requests.RequestException as exc:
                if attempt == max_retries or (exc.response is not None and exc.response.status_code != 429):
                    error_msg = str(exc)
                    try:
                        if exc.response is not None:
                            error_msg += f" - {exc.response.text}"
                    except Exception:
                        pass
                    return {"text": f"AI service error: {error_msg}"}
                time.sleep(backoff)
                backoff *= 2
