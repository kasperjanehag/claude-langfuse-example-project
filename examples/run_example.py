"""
Simple example showing OpenAI structured outputs + Langfuse.

This example demonstrates:
1. Loading input data
2. Calling an LLM agent with structured outputs
3. Viewing results in Langfuse

Run with: python examples/run_example.py
"""

import json
import os
from datetime import datetime

from agent_sdk.agents import ExampleLLMAgent
from agent_sdk.models import InputItem, ProcessedItem
from agent_sdk.utils.config import Config


def main():
    """Run example processing pipeline."""

    print("\n" + "="*70)
    print("EXAMPLE: OpenAI Structured Outputs + Langfuse")
    print("="*70 + "\n")

    # Initialize config and agent
    config = Config()
    agent = ExampleLLMAgent(config=config)

    # Generate ID for tracing related operations
    generation_id = f"example_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    print(f"Generation ID: {generation_id}")
    print(f"Langfuse URL: {config.langfuse_host}/traces")
    print()

    # Load example input data
    input_file = "data/inputs/example_items.json"
    print(f"Loading items from: {input_file}")

    with open(input_file, 'r') as f:
        items_data = json.load(f)

    items = [InputItem(**item) for item in items_data]
    print(f"Loaded {len(items)} items\n")

    # Process each item
    results = []
    for i, item in enumerate(items, 1):
        print(f"Processing item {i}/{len(items)}: {item.id}")
        print(f"  Content: {item.content[:60]}...")

        result = agent.analyze_item(item, generation_id=generation_id)

        if result:
            results.append(result)
            print(f"  ✓ Result: {result.result[:60]}...")
            if result.confidence:
                print(f"  ✓ Confidence: {result.confidence}")
        else:
            print(f"  ✗ Failed to process")
        print()

    # Save results
    output_dir = "data/outputs"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{generation_id}.json")

    with open(output_file, 'w') as f:
        json.dump(
            [result.model_dump() for result in results],
            f,
            indent=2
        )

    print(f"Saved {len(results)} results to: {output_file}")
    print(f"\n✓ Done! View traces at: {config.langfuse_host}/traces")
    print(f"  Search for generation_id: {generation_id}\n")


if __name__ == "__main__":
    main()
