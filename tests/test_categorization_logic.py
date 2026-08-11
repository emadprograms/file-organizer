import pytest
from unittest.mock import MagicMock
from src.categorization.fine_categorization import process_fine_categorization

class MockPage:
    def __init__(self, explanation, subject="", category=""):
        self.content_explanation = explanation
        self.subject = subject
        self.category = category
        self.fine_category = ""
        self.fine_category_reason = ""

class MockLLMResult:
    def __init__(self, category, reason):
        self.category = category
        self.reason = reason

def test_id_cards_vs_forms():
    # Setup mock pages where an ID card is described as a form by Pass 1
    page1 = MockPage(
        explanation="This is a form but contains National ID and CPR details for the user.",
        category="forms"
    )
    
    mock_llm_client = MagicMock()
    mock_llm_client.generate_content.return_value = MockLLMResult(
        category="02-بيانات شخصية",
        reason="It contains CPR and National ID."
    )
    
    pages = [page1]
    result = process_fine_categorization(pages, mock_llm_client)
    
    # Assert
    assert result[0].fine_category == "02-بيانات شخصية"
    # Ensure the prompt contains the critical warning
    call_args = mock_llm_client.generate_content.call_args[1]
    assert "CRITICAL WARNING:" in call_args["contents"][0]
    assert "CPR, National ID" in call_args["contents"][0]

def test_allocation_orders_vs_modifications():
    page1 = MockPage(
        explanation="This is an allocation order document but also mentions modifications to the unit.",
        category="contract"
    )
    
    mock_llm_client = MagicMock()
    mock_llm_client.generate_content.return_value = MockLLMResult(
        category="07-قرارات التخصيص",
        reason="Allocation order is the primary focus."
    )
    
    pages = [page1]
    result = process_fine_categorization(pages, mock_llm_client)
    
    assert result[0].fine_category == "07-قرارات التخصيص"

def test_rent_vs_allowances():
    page1 = MockPage(
        explanation="Details about rent and housing allowances are discussed here.",
        category="letters",
        subject="Housing Allowance Update"
    )
    
    mock_llm_client = MagicMock()
    mock_llm_client.generate_content.return_value = MockLLMResult(
        category="11-علاوة السكن",
        reason="The subject indicates it's a housing allowance update."
    )
    
    pages = [page1]
    result = process_fine_categorization(pages, mock_llm_client)
    
    assert result[0].fine_category == "11-علاوة السكن"
    # Test that subject is prepended for letters
    call_args = mock_llm_client.generate_content.call_args[1]
    assert "Subject: Housing Allowance Update" in call_args["contents"][0]

def test_checkpointing(tmp_path):
    checkpoint_path = str(tmp_path / "test_categorization.json")
    
    page1 = MockPage(explanation="Page 1")
    page2 = MockPage(explanation="Page 2")
    
    mock_llm_client = MagicMock()
    # First run processes page1 and throws error on page2
    mock_llm_client.generate_content.side_effect = [
        MockLLMResult(category="01-عقود", reason="Reason 1"),
        Exception("Crash!")
    ]
    
    pages = [page1, page2]
    # Expect page 2 to have fallback category due to crash, but let's test if checkpoint was written
    result = process_fine_categorization(pages, mock_llm_client, run_checkpoint_path=checkpoint_path)
    
    assert result[0].fine_category == "01-عقود"
    assert result[1].fine_category == "13-رسائل متنوعة" # fallback
    
    # Reset page2 to simulate resuming where page 2 needs processing again
    page2.fine_category = ""
    # We will modify the mock to not throw an exception this time
    mock_llm_client.generate_content.side_effect = [
        MockLLMResult(category="02-بيانات شخصية", reason="Reason 2")
    ]
    
    # Let's write the checkpoint to simulate it didn't process page2 at all
    import json
    with open(checkpoint_path, 'w') as f:
        json.dump({
            "processed_indices": [0],
            "pages_data": {
                "0": {"category": "01-عقود", "reason": "Reason 1"}
            }
        }, f)
        
    pages = [MockPage(explanation="Page 1"), MockPage(explanation="Page 2")]
    result2 = process_fine_categorization(pages, mock_llm_client, run_checkpoint_path=checkpoint_path)
    
    # Should only call LLM once (for page 2)
    assert mock_llm_client.generate_content.call_count == 3 # 2 from first run, 1 from second run
    assert result2[0].fine_category == "01-عقود" # Loaded from checkpoint
    assert result2[1].fine_category == "02-بيانات شخصية"
