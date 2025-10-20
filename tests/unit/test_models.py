"""Tests for data models."""

from datetime import datetime

from agent_sdk.utils.models import (
    AuditDecision,
    LineItem,
    Location,
    Message,
    MessageRole,
    ReceiptDetails,
)


def test_message_creation():
    """Test creating a message."""
    message = Message(role=MessageRole.USER, content="Hello, world!")

    assert message.role == MessageRole.USER
    assert message.content == "Hello, world!"
    assert isinstance(message.timestamp, datetime)
    assert message.metadata == {}


def test_location_creation():
    """Test creating a location."""
    location = Location(city="Vista", state="CA", zipcode="92083")

    assert location.city == "Vista"
    assert location.state == "CA"
    assert location.zipcode == "92083"


def test_line_item_creation():
    """Test creating a line item."""
    item = LineItem(
        description="SPRAY 90",
        product_code="001920056201",
        category="supplies",
        quantity="2",
        total="28.28",
    )

    assert item.description == "SPRAY 90"
    assert item.product_code == "001920056201"
    assert item.category == "supplies"
    assert item.quantity == "2"
    assert item.total == "28.28"


def test_receipt_details_creation():
    """Test creating receipt details."""
    receipt = ReceiptDetails(
        receipt_id="rec_001",
        merchant="Walmart",
        location=Location(city="Vista", state="CA", zipcode="92083"),
        time="2023-06-30T16:40:45",
        subtotal="50.77",
        tax="4.19",
        total="54.96",
        handwritten_notes=[],
    )

    assert receipt.receipt_id == "rec_001"
    assert receipt.merchant == "Walmart"
    assert receipt.location.city == "Vista"
    assert receipt.subtotal == "50.77"
    assert receipt.tax == "4.19"
    assert receipt.total == "54.96"
    assert len(receipt.handwritten_notes) == 0


def test_audit_decision_creation():
    """Test creating an audit decision."""
    decision = AuditDecision(
        receipt_id="rec_001",
        not_travel_related=True,
        amount_over_limit=True,
        math_error=False,
        handwritten_x=False,
        reasoning="Receipt is for office supplies and exceeds $50 limit",
        needs_audit=True,
        metadata={"model": "claude-3-5-sonnet-20241022"},
    )

    assert decision.receipt_id == "rec_001"
    assert decision.not_travel_related is True
    assert decision.amount_over_limit is True
    assert decision.math_error is False
    assert decision.handwritten_x is False
    assert decision.needs_audit is True
    assert "office supplies" in decision.reasoning
