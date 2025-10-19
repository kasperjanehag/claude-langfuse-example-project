"""Tests for data models."""

from datetime import datetime

from agent_sdk.utils.models import (
    AgentResponse,
    CustomerQuery,
    EvalResult,
    KnowledgeBase,
    Message,
    MessageRole,
)


def test_message_creation():
    """Test creating a message."""
    message = Message(role=MessageRole.USER, content="Hello, world!")

    assert message.role == MessageRole.USER
    assert message.content == "Hello, world!"
    assert isinstance(message.timestamp, datetime)
    assert message.metadata == {}


def test_customer_query_creation():
    """Test creating a customer query."""
    query = CustomerQuery(
        query_id="test_123",
        customer_id="cust_456",
        message="How do I reset my password?",
        context={"category": "account"},
    )

    assert query.query_id == "test_123"
    assert query.customer_id == "cust_456"
    assert query.message == "How do I reset my password?"
    assert query.context == {"category": "account"}


def test_agent_response_creation():
    """Test creating an agent response."""
    response = AgentResponse(
        response_id="resp_123",
        query_id="query_456",
        message="You can reset your password by...",
        reasoning="I based this on the documentation",
        confidence=0.95,
        sources=["kb_001"],
        metadata={"model": "claude-3-5-sonnet-20241022"},
    )

    assert response.response_id == "resp_123"
    assert response.query_id == "query_456"
    assert "reset" in response.message
    assert response.reasoning is not None
    assert response.confidence == 0.95
    assert len(response.sources) == 1


def test_eval_result_creation():
    """Test creating an evaluation result."""
    eval_result = EvalResult(
        eval_id="eval_123",
        query_id="query_456",
        response_id="resp_789",
        metric_name="faithfulness",
        score=0.85,
        explanation="Response is mostly faithful",
        passed=True,
    )

    assert eval_result.metric_name == "faithfulness"
    assert eval_result.score == 0.85
    assert eval_result.passed is True


def test_knowledge_base_creation():
    """Test creating a knowledge base entry."""
    kb = KnowledgeBase(
        id="kb_001",
        title="Password Reset",
        content="To reset your password...",
        category="account_management",
        tags=["password", "reset", "account"],
    )

    assert kb.id == "kb_001"
    assert kb.title == "Password Reset"
    assert kb.category == "account_management"
    assert len(kb.tags) == 3
