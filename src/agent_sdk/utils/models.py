"""Data models for the agent SDK."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Message role enum."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """A message in a conversation."""

    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CustomerQuery(BaseModel):
    """A customer support query."""

    query_id: str
    customer_id: str
    message: str
    context: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class AgentResponse(BaseModel):
    """An agent's response."""

    response_id: str
    query_id: str
    message: str
    reasoning: Optional[str] = None
    confidence: Optional[float] = None
    sources: Optional[List[str]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class EvalResult(BaseModel):
    """Result of an evaluation."""

    eval_id: str
    query_id: str
    response_id: str
    metric_name: str
    score: float
    explanation: Optional[str] = None
    passed: bool
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class KnowledgeBase(BaseModel):
    """A simple knowledge base entry."""

    id: str
    title: str
    content: str
    category: str
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Receipt Inspection Models
class Location(BaseModel):
    """Location information from a receipt."""

    city: Optional[str] = None
    state: Optional[str] = None
    zipcode: Optional[str] = None


class LineItem(BaseModel):
    """Line item from a receipt."""

    description: Optional[str] = None
    product_code: Optional[str] = None
    category: Optional[str] = None
    item_price: Optional[str] = None
    sale_price: Optional[str] = None
    quantity: Optional[str] = None
    total: Optional[str] = None


class ReceiptDetails(BaseModel):
    """Structured details extracted from a receipt image."""

    receipt_id: str
    merchant: Optional[str] = None
    location: Optional[Location] = None
    time: Optional[str] = None
    items: List[LineItem] = Field(default_factory=list)
    subtotal: Optional[str] = None
    tax: Optional[str] = None
    total: Optional[str] = None
    handwritten_notes: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AuditDecision(BaseModel):
    """Decision on whether a receipt needs auditing based on defined criteria."""

    receipt_id: str
    not_travel_related: bool = Field(
        description="True if the receipt is not travel-related (e.g., office supplies)"
    )
    amount_over_limit: bool = Field(
        description="True if the total amount exceeds $50"
    )
    math_error: bool = Field(
        description="True if there are math errors in the receipt (items don't sum to total)"
    )
    handwritten_x: bool = Field(
        description="True if there is an 'X' in the handwritten notes"
    )
    reasoning: str = Field(
        description="Detailed explanation for the audit decision"
    )
    needs_audit: bool = Field(
        description="Final determination if receipt needs auditing (true if any criterion is violated)"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
