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

    def generate(self, model: str, contents: list[dict[str, Any]], response_schema: type | None = None, validation_context: dict[str, Any] | None = None) -> Any:
        """Generate a structured response from the LLM.
        
        Args:
            model (str): The model identifier to use.
            contents (list[dict[str, Any]]): The list of prompt contents (text or images).
            response_schema (type | None): A Pydantic BaseModel class for structured output.
            validation_context (dict[str, Any] | None): Optional context for Pydantic validation.
            
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
        self.client = genai.Client(api_key=api_key, http_options={'timeout': 60000})

    @property
    def name(self) -> str:
        """str: The identifier name of the provider ('gemini')."""
        return self._name

    def generate(self, model: str, contents: list[dict[str, Any]], response_schema: type | None = None, validation_context: dict[str, Any] | None = None) -> Any:
        """Generate a structured response using the Gemini API.
        
        Args:
            model (str): The model identifier to use.
            contents (list[dict[str, Any]]): The list of prompt contents.
            response_schema (type | None): A Pydantic BaseModel class for structured output, or None for raw text.
            validation_context (dict[str, Any] | None): Optional context for Pydantic validation.
            
        Returns:
            Any: An instance of the response_schema, or raw text if schema is None.
        """
        kwargs = {"temperature": 0}
        if response_schema:
            kwargs["response_mime_type"] = "application/json"
            kwargs["response_schema"] = response_schema
            
        actual_model = model.replace("google/", "") if model.startswith("google/") else model
        response = self.client.models.generate_content(
            model=actual_model,
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
            
            if not response.text:
                raise ValueError("Gemini returned empty text and no parsed object. Output may have been blocked or truncated.")
                
            text = response.text.strip() # type: ignore
            json_match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
            if json_match:
                text = json_match.group(1)
            data = json.loads(text)
            return response_schema.model_validate(data, context=validation_context)
        except Exception as e:
            raw_text = getattr(response, 'text', 'No text available')
            raise ValueError(f"LLM parsing error. Raw output: {raw_text}. Error: {e}")


