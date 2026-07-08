"""LLM Provider implementations using the Strategy Pattern.

This module defines the `LLMProvider` protocol and provides concrete implementations
for Gemini, OpenRouter, and Groq. By using the strategy pattern, the core LLM orchestration
logic in `llm.py` is decoupled from the specific API clients, allowing for seamless
failover and easy integration of new models.
"""
from typing import Any, Protocol
import re
import json
import base64
from google import genai
from google.genai import types
import openai
from src.core.config import OPENROUTER_MODEL, GROQ_MODEL
import logging

logger = logging.getLogger(f"file_organizer.{__name__}")

class LLMProvider(Protocol):
    """Protocol defining the interface for an LLM provider strategy."""
    
    @property
    def name(self) -> str:
        """The identifier name of the provider."""
        ...

    def generate(self, model: str, contents: list, response_schema: type | None = None, validation_context: dict | None = None) -> Any:
        """Generate a structured response from the LLM.
        
        Args:
            model (str): The model identifier to use.
            contents (list): The list of prompt contents (text or images).
            response_schema (type): A Pydantic BaseModel class for structured output.
            validation_context (dict | None): Optional context for Pydantic validation.
            
        Returns:
            Any: An instance of the response_schema populated with the LLM's output.
        """
        ...

class GeminiProvider:
    """Concrete LLM provider implementation for Google Gemini."""
    
    def __init__(self, api_key: str):
        """Initialize the GeminiProvider.
        
        Args:
            api_key (str): The Google GenAI API key.
        """
        self._name = "gemini"
        self.client = genai.Client(api_key=api_key)

    @property
    def name(self) -> str:
        """str: The identifier name of the provider ('gemini')."""
        return self._name

    def generate(self, model: str, contents: list, response_schema: type | None = None, validation_context: dict | None = None) -> Any:
        """Generate a structured response using the Gemini API.
        
        Args:
            model (str): The model identifier to use.
            contents (list): The list of prompt contents.
            response_schema (type | None): A Pydantic BaseModel class for structured output, or None for raw text.
            validation_context (dict | None): Optional context for Pydantic validation.
            
        Returns:
            Any: An instance of the response_schema, or raw text if schema is None.
        """
        kwargs = {"temperature": 0}
        if response_schema:
            kwargs["response_mime_type"] = "application/json"
            kwargs["response_schema"] = response_schema
            
        response = self.client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(**kwargs)
        )
        
        if hasattr(response, "usage_metadata") and response.usage_metadata is not None:
            if hasattr(response.usage_metadata, "total_token_count"):
                logger.info(f"Gemini API Token Usage: {response.usage_metadata.total_token_count} total tokens")

        if not response_schema:
            return getattr(response, "text", "")
            
        try:
            if response.parsed is not None:
                # Even if parsed, we want to apply validation_context if available
                if validation_context:
                    return response_schema.model_validate(response.parsed.model_dump(), context=validation_context)
                return response.parsed
            text = response.text.strip() # type: ignore
            json_match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
            if json_match:
                text = json_match.group(1)
            data = json.loads(text)
            return response_schema.model_validate(data, context=validation_context)
        except Exception as e:
            raw_text = getattr(response, 'text', 'No text available')
            raise ValueError(f"LLM parsing error. Raw output: {raw_text}. Error: {e}")

class OpenRouterProvider:
    """Concrete LLM provider implementation for OpenRouter."""
    
    def __init__(self, api_key: str):
        """Initialize the OpenRouterProvider.
        
        Args:
            api_key (str): The OpenRouter API key.
        """
        self._name = "openrouter"
        self.client = openai.Client(api_key=api_key, base_url="https://openrouter.ai/api/v1")

    @property
    def name(self) -> str:
        """str: The identifier name of the provider ('openrouter')."""
        return self._name

    def generate(self, model: str, contents: list, response_schema: type | None = None, validation_context: dict | None = None) -> Any:
        """Generate a structured response using the OpenRouter API.
        
        Args:
            model (str): The model identifier to use.
            contents (list): The list of prompt contents.
            response_schema (type | None): A Pydantic BaseModel class for structured output.
            validation_context (dict | None): Optional context for Pydantic validation.
            
        Returns:
            Any: An instance of the response_schema or raw text.
        """
        prompt_content = []
        for part in contents:
            if isinstance(part, str):
                prompt_content.append({"type": "text", "text": part})
            elif hasattr(part, "data") and hasattr(part, "mime_type"):
                b64 = base64.b64encode(part.data).decode("utf-8")
                prompt_content.append({"type": "image_url", "image_url": {"url": f"data:{part.mime_type};base64,{b64}"}})
        
        messages = [{"role": "user", "content": prompt_content}]
        kwargs = {"model": OPENROUTER_MODEL, "messages": messages, "temperature": 0} # type: ignore
        if response_schema:
            kwargs["response_format"] = {"type": "json_object"} # type: ignore
            
        response = self.client.chat.completions.create(**kwargs)
        text = ""
        try:
            text = response.choices[0].message.content.strip() # type: ignore
            if not response_schema:
                return text
                
            json_match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
            if json_match:
                text = json_match.group(1)
            data = json.loads(text)
            return response_schema.model_validate(data, context=validation_context)
        except Exception as e:
            raise ValueError(f"LLM parsing error. Raw output: {text}. Error: {e}")

class GroqProvider:
    """Concrete LLM provider implementation for Groq."""
    
    def __init__(self, api_key: str):
        """Initialize the GroqProvider.
        
        Args:
            api_key (str): The Groq API key.
        """
        self._name = "groq"
        self.client = openai.Client(api_key=api_key, base_url="https://api.groq.com/openai/v1")

    @property
    def name(self) -> str:
        """str: The identifier name of the provider ('groq')."""
        return self._name

    def generate(self, model: str, contents: list, response_schema: type | None = None, validation_context: dict | None = None) -> Any:
        """Generate a structured response using the Groq API.
        
        Args:
            model (str): The model identifier to use.
            contents (list): The list of prompt contents.
            response_schema (type | None): A Pydantic BaseModel class for structured output.
            validation_context (dict | None): Optional context for Pydantic validation.
            
        Returns:
            Any: An instance of the response_schema or text.
        """
        prompt_content = []
        for part in contents:
            if isinstance(part, str):
                prompt_content.append({"type": "text", "text": part})
            elif hasattr(part, "data") and hasattr(part, "mime_type"):
                b64 = base64.b64encode(part.data).decode("utf-8")
                prompt_content.append({"type": "image_url", "image_url": {"url": f"data:{part.mime_type};base64,{b64}"}})
        
        messages = [{"role": "user", "content": prompt_content}]
        kwargs = {"model": GROQ_MODEL, "messages": messages, "temperature": 0} # type: ignore
        if response_schema:
            kwargs["response_format"] = {"type": "json_object"} # type: ignore
            
        response = self.client.chat.completions.create(**kwargs)
        text = ""
        try:
            text = response.choices[0].message.content.strip() # type: ignore
            if not response_schema:
                return text
                
            json_match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
            if json_match:
                text = json_match.group(1)
            data = json.loads(text)
            return response_schema.model_validate(data, context=validation_context)
        except Exception as e:
            raise ValueError(f"LLM parsing error. Raw output: {text}. Error: {e}")
