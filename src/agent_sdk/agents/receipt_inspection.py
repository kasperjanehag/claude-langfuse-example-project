"""Receipt inspection agent implementation."""

import base64
import mimetypes
import uuid
from pathlib import Path
from typing import Optional

from anthropic import Anthropic
from langfuse.decorators import langfuse_context, observe

from agent_sdk.utils.config import Config
from agent_sdk.utils.models import AuditDecision, ReceiptDetails


class ReceiptInspectionAgent:
    """
    A receipt inspection agent that extracts receipt details and makes audit decisions.

    This agent demonstrates:
    - Vision API usage for extracting structured data from images
    - Multi-step processing (extraction -> audit decision)
    - Langfuse tracing integration
    - Structured outputs with reasoning
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the receipt inspection agent.

        Args:
            config: Application configuration
        """
        self.config = config or Config()
        self.client = Anthropic(
            api_key=self.config.anthropic_api_key,
            base_url=self.config.anthropic_base_url,
        )

    @observe(name="extract_receipt_details")
    async def extract_receipt_details(
        self, image_path: str, receipt_id: Optional[str] = None
    ) -> ReceiptDetails:
        """
        Extract structured details from a receipt image.

        Args:
            image_path: Path to the receipt image file
            receipt_id: Optional receipt ID (generated if not provided)

        Returns:
            Structured receipt details
        """
        receipt_id = receipt_id or str(uuid.uuid4())

        langfuse_context.update_current_trace(
            name="receipt_inspection",
            metadata={"receipt_id": receipt_id, "image_path": image_path},
        )

        # Determine image type for data URI
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_type = "image/jpeg"  # Default fallback

        # Read and base64 encode the image
        image_data = Path(image_path).read_bytes()
        b64_image = base64.b64encode(image_data).decode("utf-8")

        extraction_prompt = """Given an image of a retail receipt, extract all relevant information and format it as a structured response.

# Task Description

Carefully examine the receipt image and identify the following key information:

1. Merchant name and any relevant store identification
2. Location information (city, state, ZIP code)
3. Date and time of purchase (format as ISO: YYYY-MM-DDTHH:MM:SS if possible)
4. All purchased items with their:
   * Item description/name (exactly as printed)
   * Item code/SKU (if present)
   * Category (infer from context: e.g., fuel, hotel, food, supplies, etc.)
   * Regular price per item (if available)
   * Sale price per item (if discounted)
   * Quantity purchased
   * Total price for the line item
5. Financial summary:
   * Subtotal before tax
   * Tax amount
   * Final total
6. Any handwritten notes or annotations on the receipt (list each separately)

## Important Guidelines

* If information is unclear or missing, return null for that field
* Format all monetary values as decimal numbers (e.g., "42.50")
* Distinguish between printed text and handwritten notes
* Be precise with amounts and totals
* For item categories, use context clues (gas station = fuel, hotel = lodging, etc.)
* Preserve exact spelling from the receipt for descriptions and product codes

Your response should be structured and complete, capturing all available information from the receipt."""

        try:
            message = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": extraction_prompt},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": mime_type,
                                    "data": b64_image,
                                },
                            },
                        ],
                    }
                ],
            )

            # Parse the response - Claude will return structured text
            response_text = message.content[0].text

            # Track token usage
            langfuse_context.update_current_observation(
                usage={
                    "input": message.usage.input_tokens,
                    "output": message.usage.output_tokens,
                    "total": message.usage.input_tokens + message.usage.output_tokens,
                }
            )

            # For now, we'll return a placeholder structure
            # In production, you'd want to use structured outputs or parse the response
            receipt_details = self._parse_receipt_details(
                response_text, receipt_id, message.usage.input_tokens, message.usage.output_tokens
            )

            return receipt_details

        except Exception as e:
            langfuse_context.update_current_observation(
                level="ERROR", status_message=str(e)
            )
            raise

    @observe(name="evaluate_receipt_for_audit")
    async def evaluate_receipt_for_audit(
        self, receipt_details: ReceiptDetails
    ) -> AuditDecision:
        """
        Determine if a receipt needs to be audited based on defined criteria.

        Audit criteria:
        1. NOT_TRAVEL_RELATED: Receipt is not for travel expenses (gas, hotel, airfare, car rental)
        2. AMOUNT_OVER_LIMIT: Total amount exceeds $50
        3. MATH_ERROR: Line items don't sum correctly to the total
        4. HANDWRITTEN_X: There is an "X" in handwritten notes

        Args:
            receipt_details: Extracted receipt details

        Returns:
            Audit decision with reasoning
        """
        langfuse_context.update_current_trace(
            session_id=receipt_details.receipt_id,
            metadata={"merchant": receipt_details.merchant, "total": receipt_details.total},
        )

        audit_prompt = """Evaluate this receipt data to determine if it needs to be audited based on the following criteria:

1. NOT_TRAVEL_RELATED:
   - IMPORTANT: For this criterion, travel-related expenses include but are not limited to: gas/fuel, hotel/lodging, airfare, or car rental.
   - If the receipt IS for a travel-related expense, set this to FALSE.
   - If the receipt is NOT for a travel-related expense (like office supplies, food, retail), set this to TRUE.
   - In other words, if the receipt shows FUEL/GAS, this would be FALSE because gas IS travel-related.

2. AMOUNT_OVER_LIMIT: The total amount exceeds $50

3. MATH_ERROR: The math for computing the total doesn't add up (line items + tax don't sum to total within reasonable rounding)

4. HANDWRITTEN_X: There is an "X" in the handwritten notes

For each criterion, determine if it is violated (true) or not (false). Provide your reasoning for each decision, and make a final determination on whether the receipt needs auditing. A receipt needs auditing if ANY of the criteria are violated.

Return a structured response with:
- Each criterion evaluation (true/false)
- Detailed reasoning explaining your evaluation
- Final audit decision (needs_audit: true/false)"""

        receipt_json = receipt_details.model_dump_json(indent=2)

        try:
            message = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=0,  # Use 0 for more deterministic decisions
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": audit_prompt},
                            {
                                "type": "text",
                                "text": f"Receipt details:\n{receipt_json}",
                            },
                        ],
                    }
                ],
            )

            response_text = message.content[0].text

            # Track token usage
            langfuse_context.update_current_observation(
                usage={
                    "input": message.usage.input_tokens,
                    "output": message.usage.output_tokens,
                    "total": message.usage.input_tokens + message.usage.output_tokens,
                }
            )

            # Parse the audit decision
            audit_decision = self._parse_audit_decision(
                response_text,
                receipt_details.receipt_id,
                message.usage.input_tokens,
                message.usage.output_tokens,
            )

            return audit_decision

        except Exception as e:
            langfuse_context.update_current_observation(
                level="ERROR", status_message=str(e)
            )
            raise

    @observe(name="process_receipt")
    async def process_receipt(
        self, image_path: str, receipt_id: Optional[str] = None
    ) -> tuple[ReceiptDetails, AuditDecision]:
        """
        End-to-end receipt processing: extract details and make audit decision.

        Args:
            image_path: Path to the receipt image
            receipt_id: Optional receipt ID

        Returns:
            Tuple of (receipt_details, audit_decision)
        """
        receipt_details = await self.extract_receipt_details(image_path, receipt_id)
        audit_decision = await self.evaluate_receipt_for_audit(receipt_details)

        return receipt_details, audit_decision

    def _parse_receipt_details(
        self, response_text: str, receipt_id: str, input_tokens: int, output_tokens: int
    ) -> ReceiptDetails:
        """
        Parse receipt details from Claude's response.

        Note: This is a simplified parser. In production, you'd want to use
        structured outputs or more sophisticated parsing.
        """
        # For now, return a basic structure
        # You would implement actual parsing logic here
        return ReceiptDetails(
            receipt_id=receipt_id,
            metadata={
                "raw_response": response_text,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "model": self.config.model,
            },
        )

    def _parse_audit_decision(
        self, response_text: str, receipt_id: str, input_tokens: int, output_tokens: int
    ) -> AuditDecision:
        """
        Parse audit decision from Claude's response.

        Note: This is a simplified parser. In production, you'd want to use
        structured outputs or more sophisticated parsing.
        """
        # Simple keyword-based parsing
        response_lower = response_text.lower()

        # Extract boolean decisions
        not_travel_related = "not_travel_related: true" in response_lower or \
                           "not travel-related: true" in response_lower
        amount_over_limit = "amount_over_limit: true" in response_lower or \
                          "amount over limit: true" in response_lower
        math_error = "math_error: true" in response_lower or \
                    "math error: true" in response_lower
        handwritten_x = "handwritten_x: true" in response_lower or \
                       "handwritten x: true" in response_lower

        needs_audit = any([not_travel_related, amount_over_limit, math_error, handwritten_x])

        return AuditDecision(
            receipt_id=receipt_id,
            not_travel_related=not_travel_related,
            amount_over_limit=amount_over_limit,
            math_error=math_error,
            handwritten_x=handwritten_x,
            reasoning=response_text,
            needs_audit=needs_audit,
            metadata={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "model": self.config.model,
            },
        )
