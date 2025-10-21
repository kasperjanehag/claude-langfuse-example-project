"""Receipt inspection agent implementation."""

import base64
import json
import mimetypes
import uuid
from pathlib import Path
from typing import Optional

from openai import OpenAI
from langfuse.decorators import langfuse_context, observe

from agent_sdk.utils.config import Config
from agent_sdk.utils.models import AuditDecision, LineItem, Location, ReceiptDetails


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
        self.client = OpenAI(
            api_key=self.config.openai_api_key,
            base_url=self.config.openai_base_url,
        )

    def _get_receipt_details_tool(self):
        """Get the tool definition for extracting receipt details."""
        return {
            "type": "function",
            "function": {
                "name": "extract_receipt_data",
                "description": "Extract structured data from a receipt image including merchant, items, amounts, and handwritten notes",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "merchant": {
                            "type": "string",
                            "description": "Name of the merchant/store"
                        },
                        "location": {
                            "type": "object",
                            "properties": {
                                "city": {"type": "string"},
                                "state": {"type": "string"},
                                "zipcode": {"type": "string"}
                            }
                        },
                        "time": {
                            "type": "string",
                            "description": "Date and time in ISO format (YYYY-MM-DDTHH:MM:SS)"
                        },
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "description": {"type": "string"},
                                    "product_code": {"type": "string"},
                                    "category": {"type": "string", "description": "e.g., fuel, hotel, food, supplies"},
                                    "item_price": {"type": "string"},
                                    "sale_price": {"type": "string"},
                                    "quantity": {"type": "string"},
                                    "total": {"type": "string"}
                                }
                            }
                        },
                        "subtotal": {"type": "string"},
                        "tax": {"type": "string"},
                        "total": {"type": "string"},
                        "handwritten_notes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of any handwritten notes or annotations"
                        }
                    },
                    "required": ["merchant", "items", "handwritten_notes"]
                }
            }
        }

    def _get_audit_decision_tool(self):
        """Get the tool definition for making audit decisions."""
        return {
            "type": "function",
            "function": {
                "name": "make_audit_decision",
                "description": "Evaluate a receipt and determine if it needs auditing based on defined criteria",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "not_travel_related": {
                            "type": "boolean",
                            "description": "True if receipt is NOT for travel expenses (gas, hotel, airfare, car rental)"
                        },
                        "amount_over_limit": {
                            "type": "boolean",
                            "description": "True if total amount exceeds $50"
                        },
                        "math_error": {
                            "type": "boolean",
                            "description": "True if line items + tax don't sum correctly to total"
                        },
                        "handwritten_x": {
                            "type": "boolean",
                            "description": "True if there is an 'X' in handwritten notes"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Detailed explanation for the audit decision"
                        },
                        "needs_audit": {
                            "type": "boolean",
                            "description": "Final determination - true if ANY criterion is violated"
                        }
                    },
                    "required": ["not_travel_related", "amount_over_limit", "math_error", "handwritten_x", "reasoning", "needs_audit"]
                }
            }
        }

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
            # Prepare messages with image for API call (OpenAI ChatML format)
            messages_payload = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": extraction_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{b64_image}"
                            },
                        },
                    ],
                }
            ]

            # Use function calling for structured outputs
            response = self.client.chat.completions.create(
                model=self.config.model,
                max_completion_tokens=self.config.max_tokens,
                tools=[self._get_receipt_details_tool()],
                tool_choice={"type": "function", "function": {"name": "extract_receipt_data"}},
                messages=messages_payload,
            )

            # Log input/output and token usage to Langfuse
            # Langfuse automatically detects and handles base64 images in data URIs
            langfuse_context.update_current_observation(
                input=messages_payload,
                output=response.model_dump(),
                usage={
                    "input": response.usage.prompt_tokens,
                    "output": response.usage.completion_tokens,
                    "total": response.usage.total_tokens,
                }
            )

            # Extract tool call from response
            message = response.choices[0].message
            if not message.tool_calls or len(message.tool_calls) == 0:
                raise ValueError("No tool calls found in OpenAI's response")

            tool_call = message.tool_calls[0]
            if tool_call.function.name != "extract_receipt_data":
                raise ValueError(f"Expected extract_receipt_data, got {tool_call.function.name}")

            # Parse the function arguments into ReceiptDetails
            function_args = json.loads(tool_call.function.arguments)
            receipt_details = self._parse_receipt_details_from_tool(
                function_args, receipt_id, response.usage.prompt_tokens, response.usage.completion_tokens
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
            # Prepare messages for API call
            messages_payload = [
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
            ]

            # Use function calling for structured outputs
            response = self.client.chat.completions.create(
                model=self.config.model,
                max_completion_tokens=self.config.max_tokens,
                tools=[self._get_audit_decision_tool()],
                tool_choice={"type": "function", "function": {"name": "make_audit_decision"}},
                messages=messages_payload,
            )

            # Log input/output and token usage to Langfuse
            langfuse_context.update_current_observation(
                input=messages_payload,
                output=response.model_dump(),
                usage={
                    "input": response.usage.prompt_tokens,
                    "output": response.usage.completion_tokens,
                    "total": response.usage.total_tokens,
                }
            )

            # Extract tool call from response
            message = response.choices[0].message
            if not message.tool_calls or len(message.tool_calls) == 0:
                raise ValueError("No tool calls found in OpenAI's response")

            tool_call = message.tool_calls[0]
            if tool_call.function.name != "make_audit_decision":
                raise ValueError(f"Expected make_audit_decision, got {tool_call.function.name}")

            # Parse the audit decision from function arguments
            function_args = json.loads(tool_call.function.arguments)
            audit_decision = self._parse_audit_decision_from_tool(
                function_args,
                receipt_details.receipt_id,
                response.usage.prompt_tokens,
                response.usage.completion_tokens,
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

    def _parse_receipt_details_from_tool(
        self, tool_input: dict, receipt_id: str, input_tokens: int, output_tokens: int
    ) -> ReceiptDetails:
        """
        Parse receipt details from Claude's tool use input.

        Args:
            tool_input: The input dictionary from Claude's tool use
            receipt_id: Receipt identifier
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens used

        Returns:
            Parsed ReceiptDetails object
        """
        # Parse location
        location_data = tool_input.get("location", {})
        location = Location(
            city=location_data.get("city"),
            state=location_data.get("state"),
            zipcode=location_data.get("zipcode"),
        ) if location_data else None

        # Parse line items
        items = []
        for item_data in tool_input.get("items", []):
            items.append(LineItem(
                description=item_data.get("description"),
                product_code=item_data.get("product_code"),
                category=item_data.get("category"),
                item_price=item_data.get("item_price"),
                sale_price=item_data.get("sale_price"),
                quantity=item_data.get("quantity"),
                total=item_data.get("total"),
            ))

        return ReceiptDetails(
            receipt_id=receipt_id,
            merchant=tool_input.get("merchant"),
            location=location,
            time=tool_input.get("time"),
            items=items,
            subtotal=tool_input.get("subtotal"),
            tax=tool_input.get("tax"),
            total=tool_input.get("total"),
            handwritten_notes=tool_input.get("handwritten_notes", []),
            metadata={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "model": self.config.model,
            },
        )

    def _parse_audit_decision_from_tool(
        self, tool_input: dict, receipt_id: str, input_tokens: int, output_tokens: int
    ) -> AuditDecision:
        """
        Parse audit decision from Claude's tool use input.

        Args:
            tool_input: The input dictionary from Claude's tool use
            receipt_id: Receipt identifier
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens used

        Returns:
            Parsed AuditDecision object
        """
        return AuditDecision(
            receipt_id=receipt_id,
            not_travel_related=tool_input.get("not_travel_related", False),
            amount_over_limit=tool_input.get("amount_over_limit", False),
            math_error=tool_input.get("math_error", False),
            handwritten_x=tool_input.get("handwritten_x", False),
            reasoning=tool_input.get("reasoning", ""),
            needs_audit=tool_input.get("needs_audit", False),
            metadata={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "model": self.config.model,
            },
        )
