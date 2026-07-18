"""Mock LLM Provider for local testing."""
import json
import re
import logging
from typing import Any

logger = logging.getLogger(f"file_organizer.{__name__}")

class MockLLMProvider:
    """Concrete LLM provider implementation for mocking responses."""
    
    def __init__(self) -> None:
        """Initialize the MockLLMProvider."""
        self._name = "mock"

    @property
    def name(self) -> str:
        """str: The identifier name of the provider."""
        return self._name

    def generate(self, model: str, contents: list[dict[str, Any]], response_schema: type | None = None, validation_context: dict[str, Any] | None = None) -> Any:
        """Generate a structured response using the mock provider.
        
        Args:
            model (str): The model identifier to use.
            contents (list[dict[str, Any]]): The list of prompt contents.
            response_schema (type | None): A Pydantic BaseModel class for structured output.
            validation_context (dict[str, Any] | None): Optional context for Pydantic validation.
            
        Returns:
            Any: An instance of the response_schema, or raw text if schema is None.
        """
        if response_schema is None:
            for content in contents:
                if isinstance(content, str) and "Raw names:" in content:
                    try:
                        start_idx = content.find("[")
                        end_idx = content.rfind("]") + 1
                        if start_idx != -1 and end_idx != -1:
                            names = json.loads(content[start_idx:end_idx])
                            if isinstance(names, list):
                                return json.dumps({name: name for name in names}, ensure_ascii=False)
                    except Exception:
                        pass
            return "{}"

        schema_name = getattr(response_schema, "__name__", "")
        if schema_name == "GroupingResponse":
            from src.core.schemas import GroupingResponse, GroupEntry
            content_str = str(contents)
            m = re.search(r'Chunk range: Page (\d+) to Page (\d+)', content_str)
            if m:
                start, end = int(m.group(1)), int(m.group(2))
            else:
                start, end = 0, 0
            return GroupingResponse.model_construct(groups=[GroupEntry(start_page=start, end_page=end, reason="mock skip-llm", brief_arabic_title="عنوان تجريبي")])
        elif schema_name == "RoutingResponse":
            try:
                from src.routing.router import RoutingResponse
                return RoutingResponse.model_construct(selected_folder="رسائل متنوعة", reason="mock skip-llm")
            except ImportError:
                pass
        
        # Fallback for dynamic/unknown schemas
        try:
            if hasattr(response_schema, "model_construct"):
                return response_schema.model_construct()
            return response_schema()
        except Exception:
            return None
