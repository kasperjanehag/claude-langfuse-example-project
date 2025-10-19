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
