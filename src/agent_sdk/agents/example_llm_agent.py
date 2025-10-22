"""
Example LLM agent showing patterns for OpenAI structured outputs + Langfuse.

This is a simple example showing:
- How to call OpenAI with structured outputs
- How to use Langfuse for observability
- How to handle errors
- How to work with Pydantic models

CUSTOMIZE THIS:
- Replace with your own use case
- Update prompts for your domain
- Add your business logic
"""

from typing import Optional

import openai
from langfuse.decorators import langfuse_context, observe

from agent_sdk.models.domain_models import InputItem, ProcessedItem
from agent_sdk.models.llm_responses import ExampleAnalysisResponse
from agent_sdk.utils.config import Config


class ExampleLLMAgent:
    """
    Example agent that uses OpenAI structured outputs with Langfuse tracing.

    This demonstrates the core patterns:
    1. Initialize OpenAI client with config
    2. Use @observe decorator for Langfuse tracing
    3. Call LLM with structured outputs (response_format parameter)
    4. Handle errors properly
    5. Update Langfuse traces with metadata
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the agent.

        Args:
            config: Application configuration (API keys, model, etc.)
        """
        self.config = config or Config()
        self.client = openai.OpenAI(
            api_key=self.config.openai_api_key,
            base_url=self.config.openai_base_url
        )

    @observe(name="analyze_item")
    def analyze_item(
        self,
        item: InputItem,
        generation_id: Optional[str] = None
    ) -> Optional[ProcessedItem]:
        """
        Example method showing how to call LLM with structured outputs.

        Args:
            item: Input item to analyze
            generation_id: Optional ID for tracing related calls

        Returns:
            ProcessedItem if successful, None otherwise
        """

        # Build prompt
        prompt = self._build_prompt(item)

        # Update Langfuse trace with metadata
        langfuse_context.update_current_observation(
            metadata={
                "generation_id": generation_id,
                "item_id": item.id,
            }
        )

        # Call OpenAI with structured output
        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.config.model,
                max_completion_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
                response_format=ExampleAnalysisResponse,  # This enforces the structure
            )

            # Extract parsed Pydantic object
            response: ExampleAnalysisResponse = completion.choices[0].message.parsed

            # Process the response into your output format
            result = self._process_response(response, item)

            # Update trace with result
            langfuse_context.update_current_observation(
                metadata={
                    "result_id": result.id if result else None,
                    "confidence": response.confidence,
                }
            )

            return result

        except Exception as e:
            # Handle errors - print for debugging, log to Langfuse
            import traceback
            error_details = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            print(f"\n{'='*70}")
            print(f"ERROR in analyze_item for {item.id}:")
            print(error_details)
            print(f"{'='*70}\n")

            langfuse_context.update_current_observation(
                metadata={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "traceback": traceback.format_exc()
                }
            )
            return None

    def _build_prompt(self, item: InputItem) -> str:
        """
        Build prompt for the LLM.

        CUSTOMIZE THIS with your domain-specific instructions.
        """
        prompt = f"""You are an expert analyst. Analyze the following item and provide insights.

ITEM TO ANALYZE:
ID: {item.id}
Content: {item.content}
Metadata: {item.metadata}

YOUR TASK:
1. Read and understand the content
2. Identify key points
3. Determine overall sentiment
4. Provide a confidence score for your analysis
5. Explain your reasoning

Return your analysis in the specified JSON format.
"""
        return prompt

    def _process_response(
        self,
        response: ExampleAnalysisResponse,
        item: InputItem
    ) -> ProcessedItem:
        """
        Convert LLM response into your output format.

        CUSTOMIZE THIS for your use case.
        """
        result = ProcessedItem(
            id=f"result-{item.id}",
            input_id=item.id,
            result=response.summary,
            confidence=response.confidence,
            details={
                "key_points": response.key_points or [],
                "sentiment": response.sentiment,
                "reasoning": response.reasoning,
            }
        )
        return result
