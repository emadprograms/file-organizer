import unittest
from unittest.mock import MagicMock
from pydantic import ValidationError
from src.core.schemas import DocumentGroup
from src.routing.router import route_document, RoutingValidationError
from src.routing.config import (
    SINGLE_MATCH, 
    DIRECT_ROUTING_MAP, 
    FORM_CATEGORIES, 
    LETTER_CATEGORIES, 
    FORM_FOLDERS, 
    LETTER_FOLDERS,
    FOLDER_ROUTING
)

class MockLLMClient:
    def __init__(self, response_value=None):
        self.response_value = response_value
        self.call_count = 0

    def generate_content(self, contents, response_schema, validation_context=None, **kwargs):
        self.call_count += 1
        if self.response_value is None:
            return None
        
        # If we are simulating a failure, we must raise the error the router expects
        if validation_context and 'allowed_folders' in validation_context:
            allowed = validation_context['allowed_folders']
            if self.response_value['selected_folder'] not in allowed:
                # Simulate the ValidationError that the router's try/except block catches
                # We use a simple ValueError here as the router catches (ValidationError, ValueError)
                raise ValueError(f"Selected folder '{self.response_value['selected_folder']}' is not in the allowed list")
        
        # For success, return a mock object that behaves like a Pydantic model
        mock_resp = MagicMock()
        mock_resp.selected_folder = self.response_value['selected_folder']
        mock_resp.reason = self.response_value['reason']
        return mock_resp

class TestPhase12Finalization(unittest.TestCase):
    def setUp(self):
        self.llm_client = MockLLMClient()
        self.base_group = DocumentGroup(
            category="unknown",
            brief_arabic_title="Test Doc",
            reason="Test Reason",
            start_page=1,
            end_page=1,
            primary_tenant="Test Tenant",
            dates=["2023-01-01"]
        )

    def test_single_match_direct_routing(self):
        """Verify that categories in SINGLE_MATCH route directly without LLM."""
        # Pick a category that is in SINGLE_MATCH (e.g., CONTRACT usually is)
        cat = list(SINGLE_MATCH)[0]
        group = self.base_group.model_copy(update={"category": cat})
        
        folder, is_direct = route_document(group, self.llm_client)
        
        self.assertTrue(is_direct)
        self.assertIn(folder, FOLDER_ROUTING.keys())
        self.assertEqual(len([f for f, d in FOLDER_ROUTING.items() if cat in d['cats']]), 1)

    def test_direct_routing_map_routing(self):
        """Verify that categories in DIRECT_ROUTING_MAP route directly."""
        cat = "contract" # Normalized key in DIRECT_ROUTING_MAP
        group = self.base_group.model_copy(update={"category": cat})
        
        folder, is_direct = route_document(group, self.llm_client)
        
        self.assertTrue(is_direct)
        self.assertEqual(folder, DIRECT_ROUTING_MAP[cat])

    def test_form_constrained_routing_success(self):
        """Verify that categories in FORM_CATEGORIES use constrained routing when NOT in SINGLE_MATCH."""
        cat = list(FORM_CATEGORIES)[0]
        group = self.base_group.model_copy(update={"category": cat.lower()})
        
        # Force the category to NOT be a single match for this test
        with unittest.mock.patch('src.routing.router.SINGLE_MATCH', set()):
            valid_folder = list(FORM_FOLDERS)[0]
            self.llm_client.response_value = {"selected_folder": valid_folder, "reason": "Valid"}
            
            folder, is_direct = route_document(group, self.llm_client)
            
            self.assertFalse(is_direct)
            self.assertEqual(folder, valid_folder)

    def test_form_constrained_routing_invalid(self):
        """Verify that categories in FORM_CATEGORIES fail if LLM returns folder outside FORM_FOLDERS."""
        cat = list(FORM_CATEGORIES)[0]
        group = self.base_group.model_copy(update={"category": cat.lower()})
        
        with unittest.mock.patch('src.routing.router.SINGLE_MATCH', set()):
            all_folders = set(FOLDER_ROUTING.keys())
            invalid_folder = list(all_folders - FORM_FOLDERS)[0]
            
            self.llm_client.response_value = {"selected_folder": invalid_folder, "reason": "Invalid"}
            
            with self.assertRaises(RoutingValidationError):
                route_document(group, self.llm_client)

    def test_letter_constrained_routing_success(self):
        """Verify that categories in LETTER_CATEGORIES use constrained routing when NOT in SINGLE_MATCH."""
        cat = list(LETTER_CATEGORIES)[0]
        group = self.base_group.model_copy(update={"category": cat.lower()})
        
        with unittest.mock.patch('src.routing.router.SINGLE_MATCH', set()):
            valid_folder = list(LETTER_FOLDERS)[0]
            self.llm_client.response_value = {"selected_folder": valid_folder, "reason": "Valid"}
            
            folder, is_direct = route_document(group, self.llm_client)
            
            self.assertFalse(is_direct)
            self.assertEqual(folder, valid_folder)

    def test_letter_constrained_routing_invalid(self):
        """Verify that categories in LETTER_CATEGORIES fail if LLM returns folder outside LETTER_FOLDERS."""
        cat = list(LETTER_CATEGORIES)[0]
        group = self.base_group.model_copy(update={"category": cat.lower()})
        
        with unittest.mock.patch('src.routing.router.SINGLE_MATCH', set()):
            all_folders = set(FOLDER_ROUTING.keys())
            invalid_folder = list(all_folders - LETTER_FOLDERS)[0]
            
            self.llm_client.response_value = {"selected_folder": invalid_folder, "reason": "Invalid"}
            
            with self.assertRaises(RoutingValidationError):
                route_document(group, self.llm_client)

    def test_unknown_category_failure(self):
        """Verify that a category not matching any known routing path raises RoutingValidationError."""
        group = self.base_group.model_copy(update={"category": "completely_unknown_cat"})
        
        with self.assertRaises(RoutingValidationError):
            route_document(group, self.llm_client)

    def test_routing_priority(self):
        """Verify the priority: SINGLE_MATCH -> DIRECT_ROUTING_MAP -> Constrained."""
        # 1. Category in both SINGLE_MATCH and DIRECT_ROUTING_MAP (if any)
        # Let's use a category that we know is in SINGLE_MATCH
        cat = list(SINGLE_MATCH)[0]
        group = self.base_group.model_copy(update={"category": cat.lower()})
        
        folder, is_direct = route_document(group, self.llm_client)
        self.assertTrue(is_direct, "SINGLE_MATCH should take priority and be direct")

if __name__ == "__main__":
    unittest.main()
