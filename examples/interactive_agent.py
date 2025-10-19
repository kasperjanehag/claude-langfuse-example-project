"""
Interactive demo of the customer support agent.

This script provides an interactive CLI where you can:
1. Ask questions to the agent in real-time
2. See responses with reasoning
3. View Langfuse traces
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
from rich.prompt import Prompt

console = Console()


def load_knowledge_base(path: Path) -> list[KnowledgeBase]:
    """Load knowledge base from JSON file."""
    with open(path) as f:
        data = json.load(f)
    return [KnowledgeBase(**item) for item in data]


async def main():
    """Run interactive customer support agent."""
    console.print(Panel.fit("[bold blue]Interactive Customer Support Agent[/bold blue]"))
    console.print("\n[cyan]Type 'quit' or 'exit' to end the session[/cyan]\n")

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
    knowledge_base = load_knowledge_base(kb_path)
    console.print(f"[green]✓ Loaded {len(knowledge_base)} knowledge base entries[/green]\n")

    # Initialize agent
    agent = CustomerSupportAgent(config=config, knowledge_base=knowledge_base)

    # Interactive loop
    while True:
        # Get user input
        user_query = Prompt.ask("\n[bold cyan]Your question[/bold cyan]")

        if user_query.lower() in ["quit", "exit"]:
            console.print("\n[yellow]Thanks for using the customer support agent![/yellow]")
            break

        if not user_query.strip():
            continue

        # Create query
        query = CustomerQuery(
            query_id=str(uuid.uuid4()), customer_id="interactive_user", message=user_query
        )

        # Process query
        console.print("\n[dim]Processing...[/dim]")
        response = await agent.handle_query(query)

        # Display response
        console.print(Panel(response.message, title="[bold green]Agent Response[/bold green]"))

        if response.reasoning:
            console.print(
                Panel(
                    response.reasoning,
                    title="[bold yellow]Reasoning[/bold yellow]",
                    border_style="yellow",
                )
            )

        # Show trace link if Langfuse is configured
        if config.langfuse_public_key:
            console.print(
                f"\n[dim]Trace: {config.langfuse_host}/traces/{query.query_id}[/dim]"
            )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Session ended[/yellow]")
