"""
Example script to run evaluations on the customer support agent.

This demonstrates the eval-driven development workflow:
1. Load test cases with ground truth
2. Run the agent on each test case
3. Evaluate responses using multiple metrics
4. Track results in Langfuse
5. Generate evaluation report
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent_sdk.agents.customer_support import CustomerSupportAgent
from agent_sdk.evals.evaluator import Evaluator
from agent_sdk.utils.config import Config
from agent_sdk.utils.models import KnowledgeBase
from rich.console import Console

console = Console()


def load_knowledge_base(path: Path) -> list[KnowledgeBase]:
    """Load knowledge base from JSON file."""
    with open(path) as f:
        data = json.load(f)
    return [KnowledgeBase(**item) for item in data]


def load_test_cases(path: Path) -> list[dict]:
    """Load test cases from JSON file."""
    with open(path) as f:
        return json.load(f)


async def main():
    """Run evaluation on the customer support agent."""
    console.print("\n[bold blue]═══ Customer Support Agent Evaluation ═══[/bold blue]\n")

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
    console.print(f"[cyan]Loading knowledge base from {kb_path}...[/cyan]")
    knowledge_base = load_knowledge_base(kb_path)
    console.print(f"[green]✓ Loaded {len(knowledge_base)} knowledge base entries[/green]")

    # Load test cases
    test_cases_path = Path(__file__).parent.parent / "data" / "datasets" / "test_cases.json"
    console.print(f"[cyan]Loading test cases from {test_cases_path}...[/cyan]")
    test_cases = load_test_cases(test_cases_path)
    console.print(f"[green]✓ Loaded {len(test_cases)} test cases[/green]")

    # Initialize agent
    console.print("\n[cyan]Initializing customer support agent...[/cyan]")
    agent = CustomerSupportAgent(config=config, knowledge_base=knowledge_base)
    console.print("[green]✓ Agent initialized[/green]")

    # Initialize evaluator
    console.print("[cyan]Initializing evaluator...[/cyan]")
    evaluator = Evaluator(config=config)
    console.print("[green]✓ Evaluator initialized[/green]")

    # Set up output path
    output_dir = Path(__file__).parent.parent / "eval_results"
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"eval_results_{timestamp}.json"

    # Run evaluation
    summary = await evaluator.run_evaluation(
        agent=agent, test_cases=test_cases, output_path=output_path
    )

    # Display final message
    console.print(
        f"\n[bold green]Evaluation complete! Pass rate: {summary['pass_rate']:.1%}[/bold green]"
    )

    if config.langfuse_public_key:
        console.print(
            f"\n[cyan]View detailed traces in Langfuse: {config.langfuse_host}[/cyan]"
        )


if __name__ == "__main__":
    asyncio.run(main())
