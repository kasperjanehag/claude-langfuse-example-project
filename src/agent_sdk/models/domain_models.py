"""
Pydantic models for your domain - Example Template.

CUSTOMIZE THIS ENTIRELY FOR YOUR USE CASE:
- Replace these example models with your own domain models
- Add/remove fields as needed
- Update descriptions and examples

These are just examples showing the pattern of using Pydantic models
with OpenAI structured outputs.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class InputItem(BaseModel):
    """
    Example input model - replace with your domain-specific input.

    This could represent anything:
    - Documents to process
    - Customer requests
    - Data to analyze
    - Tasks to complete
    """

    id: str = Field(..., description="Unique identifier")
    content: str = Field(..., description="Main content/text")
    metadata: Optional[dict] = Field(None, description="Any additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "item-001",
                "content": "Example content here",
                "metadata": {"source": "system-a", "priority": "high"}
            }
        }


class ProcessedItem(BaseModel):
    """
    Example output model - replace with your domain-specific output.

    This could represent:
    - Analysis results
    - Generated content
    - Extracted information
    - Recommendations
    """

    id: str = Field(..., description="Unique identifier")
    input_id: str = Field(..., description="ID of input this came from")
    result: str = Field(..., description="Main result/output")
    confidence: Optional[float] = Field(None, description="Confidence score if applicable")
    details: Optional[dict] = Field(None, description="Additional details")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "result-001",
                "input_id": "item-001",
                "result": "Processed result here",
                "confidence": 0.95,
                "details": {"method": "llm-analysis"}
            }
        }


class ProcessingContext(BaseModel):
    """
    Example context model for customizing processing.

    Add fields that affect how your processing should work.
    """

    user_id: Optional[str] = Field(None, description="User requesting processing")
    parameters: Optional[dict] = Field(None, description="Processing parameters")
    preferences: Optional[dict] = Field(None, description="User preferences")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-123",
                "parameters": {"max_length": 500},
                "preferences": {"format": "detailed"}
            }
        }
