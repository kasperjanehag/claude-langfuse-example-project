"""
Pydantic models for LLM structured output responses - Example Template.

These models define what structure you want the LLM to return.
When using OpenAI's structured outputs, the LLM will return a JSON
that matches these Pydantic models exactly.

CUSTOMIZE THIS:
- Define response models that match what you need from the LLM
- Use Field() to provide descriptions that help the LLM understand what to return
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class ExampleAnalysisResponse(BaseModel):
    """
    Example LLM response model for analysis tasks.

    Replace this with your own response structure.
    """

    summary: str = Field(description="Brief summary of the analysis (2-3 sentences)")
    key_points: Optional[List[str]] = Field(
        default=None,
        description="List of key points identified"
    )
    sentiment: Optional[str] = Field(
        default=None,
        description="Overall sentiment: positive, negative, or neutral"
    )
    confidence: Optional[float] = Field(
        default=None,
        description="Confidence score between 0.0 and 1.0"
    )
    reasoning: str = Field(description="Explanation of the analysis (2-3 sentences)")


class ExampleClassificationResponse(BaseModel):
    """
    Example LLM response model for classification tasks.

    Replace this with your own response structure.
    """

    category: str = Field(description="The primary category")
    subcategories: Optional[List[str]] = Field(
        default=None,
        description="List of subcategories if applicable"
    )
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    explanation: str = Field(description="Why this classification was chosen (2-3 sentences)")


class ExampleExtractionResponse(BaseModel):
    """
    Example LLM response model for information extraction tasks.

    Replace this with your own response structure.
    """

    entities: Optional[List[dict]] = Field(
        default=None,
        description="List of entities found, each with 'type', 'value', and 'context'"
    )
    relationships: Optional[List[dict]] = Field(
        default=None,
        description="List of relationships found, each with 'source', 'relation', 'target'"
    )
    summary: str = Field(description="Summary of extracted information")
