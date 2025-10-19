"""
Example script to run the customer support agent.

This demonstrates how to:
1. Load a knowledge base
2. Initialize the agent
3. Process a customer query
4. View the response with tracing
"""

import asyncio
import json
import sys
import uuid
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent_sdk.agents.customer_support import CustomerSupportAgent
from agent_sdk.utils.config import Config
from agent_sdk.utils.models import CustomerQuery, KnowledgeBase
from rich.console import Console
from rich.panel import Panel

console = Console()


def load_knowledge_base(path: Path) -> list[KnowledgeBase]:
    """Load knowledge base from JSON file."""
    with open(path) as f:
        data = json.load(f)
    return [KnowledgeBase(**item) for item in data]


async def main():
    """Run a simple customer support query."""
    console.print(Panel.fit("[bold blue]Customer Support Agent Demo[/bold blue]"))

    # Load configuration
    config = Config()

    # Check API key
    if not config.anthropic_api_key:
        console.print(
            "[red]Error: ANTHROPIC_API_KEY not set. Please set it in your .env file.[/red]"
        )
        return

    # Load knowledge base
    kb_path = Path(__file__).parent.parent / "data" / "datasets" / "knowledge_base.json"
    console.print(f"\n[cyan]Loading knowledge base from {kb_path}...[/cyan]")
    knowledge_base = load_knowledge_base(kb_path)
    console.print(f"[green]Loaded {len(knowledge_base)} knowledge base entries[/green]")

    # Initialize agent
    agent = CustomerSupportAgent(config=config, knowledge_base=knowledge_base)

    # Create a sample query
    query = CustomerQuery(
        query_id=str(uuid.uuid4()),
        customer_id="demo_customer",
        message="How do I reset my password?",
    )

    console.print(f"\n[bold]Customer Query:[/bold] {query.message}\n")

    # Process query
    console.print("[cyan]Processing query with agent...[/cyan]\n")
    response = await agent.handle_query(query)

    # Display response
    console.print(Panel(response.message, title="[bold green]Agent Response[/bold green]"))

    if response.reasoning:
        console.print(
            Panel(
                response.reasoning,
                title="[bold yellow]Agent Reasoning[/bold yellow]",
                border_style="yellow",
            )
        )

    # Display metadata
    console.print("\n[bold]Metadata:[/bold]")
    console.print(f"  Response ID: {response.response_id}")
    console.print(f"  Model: {response.metadata.get('model', 'N/A')}")
    console.print(f"  Input Tokens: {response.metadata.get('input_tokens', 'N/A')}")
    console.print(f"  Output Tokens: {response.metadata.get('output_tokens', 'N/A')}")

    # Langfuse link
    if config.langfuse_public_key:
        console.print(
            f"\n[cyan]View trace in Langfuse: {config.langfuse_host}/traces/{query.query_id}[/cyan]"
        )
    else:
        console.print(
            "\n[yellow]Tip: Set up Langfuse to view detailed traces of agent execution[/yellow]"
        )


if __name__ == "__main__":
    asyncio.run(main())
