"""
This file contains the code to talk to different AI models.
Instead of having one giant file, we separated each AI service (like Gemini, OpenRouter, and Groq)
into its own dedicated block of code here. This makes it very easy to add new AI models later.
"""
from typing import Any, Protocol
import re
import json
import base64
from google import genai
from google.genai import types
import openai
from src.config import OPENROUTER_MODEL, GROQ_MODEL

class LLMProvider(Protocol):
    @property
    def name(self) -> str:
        ...

    def generate(self, model: str, contents: list, response_schema: type) -> Any:
        ...

class GeminiProvider:
    def __init__(self, api_key: str):
        self._name = "gemini"
        self.client = genai.Client(api_key=api_key)

    @property
    def name(self) -> str:
        return self._name

    def generate(self, model: str, contents: list, response_schema: type) -> Any:
        response = self.client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=0
            )
        )
        if response.parsed is not None:
            return response.parsed
        text = response.text.strip() # type: ignore
        json_match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
        data = json.loads(text)
        return response_schema(**data)

class OpenRouterProvider:
    def __init__(self, api_key: str):
        self._name = "openrouter"
        self.client = openai.Client(api_key=api_key, base_url="https://openrouter.ai/api/v1")

    @property
    def name(self) -> str:
        return self._name

    def generate(self, model: str, contents: list, response_schema: type) -> Any:
        prompt_content = []
        for part in contents:
            if isinstance(part, str):
                prompt_content.append({"type": "text", "text": part})
            elif hasattr(part, "data") and hasattr(part, "mime_type"):
                b64 = base64.b64encode(part.data).decode("utf-8")
                prompt_content.append({"type": "image_url", "image_url": {"url": f"data:{part.mime_type};base64,{b64}"}})
        
        messages = [{"role": "user", "content": prompt_content}]
        response = self.client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=messages, # type: ignore
            response_format={"type": "json_object"},
            temperature=0
        )
        text = response.choices[0].message.content.strip() # type: ignore
        json_match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
        data = json.loads(text)
        return response_schema(**data)

class GroqProvider:
    def __init__(self, api_key: str):
        self._name = "groq"
        self.client = openai.Client(api_key=api_key, base_url="https://api.groq.com/openai/v1")

    @property
    def name(self) -> str:
        return self._name

    def generate(self, model: str, contents: list, response_schema: type) -> Any:
        prompt_content = []
        for part in contents:
            if isinstance(part, str):
                prompt_content.append({"type": "text", "text": part})
            elif hasattr(part, "data") and hasattr(part, "mime_type"):
                b64 = base64.b64encode(part.data).decode("utf-8")
                prompt_content.append({"type": "image_url", "image_url": {"url": f"data:{part.mime_type};base64,{b64}"}})
        
        messages = [{"role": "user", "content": prompt_content}]
        response = self.client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages, # type: ignore
            response_format={"type": "json_object"},
            temperature=0
        )
        text = response.choices[0].message.content.strip() # type: ignore
        json_match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
        data = json.loads(text)
        return response_schema(**data)
