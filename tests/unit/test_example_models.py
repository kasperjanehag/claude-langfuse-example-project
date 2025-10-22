"""
Example tests for Pydantic models.

CUSTOMIZE THIS:
- Add your own model tests
- Test validation logic
- Test serialization/deserialization
"""

from agent_sdk.models import InputItem, ProcessedItem


def test_input_item_creation():
    """Test creating an InputItem."""
    item = InputItem(
        id="test-001",
        content="Test content",
        metadata={"source": "test"}
    )

    assert item.id == "test-001"
    assert item.content == "Test content"
    assert item.metadata["source"] == "test"


def test_processed_item_creation():
    """Test creating a ProcessedItem."""
    item = ProcessedItem(
        id="result-001",
        input_id="test-001",
        result="Processed result",
        confidence=0.95,
        details={"method": "test"}
    )

    assert item.id == "result-001"
    assert item.input_id == "test-001"
    assert item.result == "Processed result"
    assert item.confidence == 0.95


def test_model_serialization():
    """Test model serialization to dict and JSON."""
    item = InputItem(
        id="test-001",
        content="Test content"
    )

    # Test dict conversion
    item_dict = item.model_dump()
    assert isinstance(item_dict, dict)
    assert item_dict["id"] == "test-001"

    # Test JSON serialization
    item_json = item.model_dump_json()
    assert isinstance(item_json, str)
    assert "test-001" in item_json


def test_model_deserialization():
    """Test model deserialization from dict."""
    data = {
        "id": "test-001",
        "content": "Test content",
        "metadata": {"source": "test"}
    }

    item = InputItem(**data)
    assert item.id == "test-001"
    assert item.content == "Test content"
