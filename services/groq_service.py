import os
import requests
import json
import time
import random
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "..", ".env"))

def to_lowercase_types(obj):
    if isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            if k == "type" and isinstance(v, str):
                new_dict[k] = v.lower()
            else:
                new_dict[k] = to_lowercase_types(v)
        return new_dict
    elif isinstance(obj, list):
        return [to_lowercase_types(item) for item in obj]
    else:
        return obj

class GroqService:
    def __init__(self, model_name=None):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not model_name:
            model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        
        # Support fallback if pro model requested
        if model_name == "gemini-2.5-pro":
            model_name = "llama-3.3-70b-versatile"
        elif model_name == "gemini-2.5-flash":
            model_name = "llama-3.3-70b-versatile"
            
        self.model_name = model_name
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"

    def analyze(self, prompt):
        if not self.api_key or self.api_key.strip() == "" or "your_" in self.api_key.lower():
            return "Groq API key is not configured or is a placeholder. Please update the .env file with a valid Groq API key."

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 800
        }

        max_retries = 2
        backoff = 2.0
        
        for attempt in range(max_retries + 1):
            try:
                response = requests.post(self.endpoint, json=payload, headers=headers, timeout=30)
                if response.status_code == 429 and attempt < max_retries:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                if "choices" in data and data["choices"]:
                    choice = data["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        return choice["message"]["content"]
                return "No response returned from Groq."
            except requests.RequestException as exc:
                if attempt == max_retries:
                    return f"AI service error: {exc}"
                time.sleep(backoff)
                backoff *= 2

    def analyze_with_history(self, contents, system_instruction=None, tools=None):
        if not self.api_key or self.api_key.strip() == "" or "your_" in self.api_key.lower():
            return {"text": "Groq API key is not configured or is a placeholder. Please update the .env file with a valid Groq API key."}

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # 1. Translate Gemini's contents structure to OpenAI format
        openai_messages = []
        
        if system_instruction:
            openai_messages.append({"role": "system", "content": system_instruction})

        # Track tool call IDs to link function responses correctly
        tool_call_ids = {}

        for message in contents:
            gemini_role = message.get("role", "user")
            role = "assistant" if gemini_role == "model" else "user"
            
            parts = message.get("parts", [])
            if not parts:
                continue

            msg_obj = {"role": role}
            
            # Check the contents of the parts
            for part in parts:
                if "text" in part:
                    msg_obj["content"] = part["text"]
                elif "functionCall" in part:
                    fc = part["functionCall"]
                    # Generate a unique tool call ID
                    call_id = f"call_{int(time.time())}_{random.randint(1000, 9999)}"
                    # Store mapping for the next tool response turn
                    tool_call_ids[fc["name"]] = call_id
                    
                    msg_obj["tool_calls"] = [
                        {
                            "id": call_id,
                            "type": "function",
                            "function": {
                                "name": fc["name"],
                                "arguments": json.dumps(fc["args"])
                            }
                        }
                    ]
                elif "functionResponse" in part:
                    fr = part["functionResponse"]
                    # Retrieve the correct call_id matching this function name
                    call_id = tool_call_ids.get(fr["name"], f"call_fallback_{random.randint(1000, 9999)}")
                    
                    msg_obj = {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": fr["name"],
                        "content": json.dumps(fr["response"])
                    }

            openai_messages.append(msg_obj)

        payload = {
            "model": self.model_name,
            "messages": openai_messages,
            "temperature": 0.7,
            "max_tokens": 800
        }

        # 2. Translate Gemini's tools to OpenAI format
        if tools:
            openai_tools = []
            for tool_container in tools:
                if "functionDeclarations" in tool_container:
                    for fd in tool_container["functionDeclarations"]:
                        openai_tools.append({
                            "type": "function",
                            "function": {
                                "name": fd["name"],
                                "description": fd["description"],
                                "parameters": to_lowercase_types(fd["parameters"])
                            }
                        })
            if openai_tools:
                payload["tools"] = openai_tools

        max_retries = 2
        backoff = 2.0
        
        for attempt in range(max_retries + 1):
            try:
                response = requests.post(self.endpoint, json=payload, headers=headers, timeout=30)
                if response.status_code == 429 and attempt < max_retries:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                if "choices" in data and data["choices"]:
                    choice = data["choices"][0]
                    message = choice.get("message", {})
                    
                    if "tool_calls" in message and message["tool_calls"]:
                        tc = message["tool_calls"][0]
                        func = tc.get("function", {})
                        func_name = func.get("name")
                        func_args_str = func.get("arguments", "{}")
                        
                        try:
                            func_args = json.loads(func_args_str)
                        except Exception:
                            func_args = {}
                            
                        return {
                            "functionCall": {
                                "name": func_name,
                                "args": func_args
                            }
                        }
                    
                    if "content" in message:
                        return {"text": message["content"]}
                        
                return {"text": "No response returned from Groq."}
            except requests.RequestException as exc:
                if attempt == max_retries:
                    error_msg = str(exc)
                    try:
                        if exc.response is not None:
                            error_msg += f" - {exc.response.text}"
                    except Exception:
                        pass
                    return {"text": f"AI service error: {error_msg}"}
                time.sleep(backoff)
                backoff *= 2
