"""Example script demonstrating receipt inspection agent."""

import asyncio
import json
import sys
from pathlib import Path

from rich import print
from rich.console import Console
from rich.table import Table

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent_sdk.agents.receipt_inspection import ReceiptInspectionAgent
from agent_sdk.utils.config import Config
from agent_sdk.utils.langfuse_check import require_langfuse

console = Console()


async def main():
    """Run receipt inspection example."""
    # Require Langfuse to be available
    require_langfuse()

    # Initialize config and agent
    config = Config()
    agent = ReceiptInspectionAgent(config=config)

    console.print("[bold cyan]Receipt Inspection Agent Demo[/bold cyan]\n")

    # Example: Process a receipt from the Roboflow test set
    example_image_path = "data/test/images/Gas_20240605_164059_Raven_Scan_3_jpeg.rf.a02f4219788648c9533c802f98d68ed7.jpg"
    from datetime import datetime
    receipt_id = f"example_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    console.print(f"[yellow]Processing receipt image:[/yellow] {example_image_path}\n")

    try:
        # Use the process_receipt method which automatically nests both operations
        console.print("[bold]Processing receipt (extract + audit)...[/bold]")
        receipt_details, audit_decision = await agent.process_receipt(
            image_path=example_image_path,
            receipt_id=receipt_id
        )

        # Display extraction results
        console.print("[green]Receipt details extracted successfully![/green]\n")
        console.print("[bold]Extracted Details:[/bold]")
        print(receipt_details.model_dump_json(indent=2))
        console.print()

        # Display audit decision
        console.print("[green]Audit evaluation complete![/green]\n")

        # Create a nice table for audit criteria
        table = Table(title="Audit Decision")
        table.add_column("Criterion", style="cyan")
        table.add_column("Result", style="magenta")

        table.add_row("Not Travel Related", "✓" if audit_decision.not_travel_related else "✗")
        table.add_row("Amount Over $50", "✓" if audit_decision.amount_over_limit else "✗")
        table.add_row("Math Error", "✓" if audit_decision.math_error else "✗")
        table.add_row("Handwritten X", "✓" if audit_decision.handwritten_x else "✗")
        table.add_row(
            "[bold]Needs Audit[/bold]",
            f"[bold]{'YES' if audit_decision.needs_audit else 'NO'}[/bold]"
        )

        console.print(table)
        console.print(f"\n[bold]Reasoning:[/bold] {audit_decision.reasoning}\n")

        # Show token usage
        if "input_tokens" in audit_decision.metadata:
            console.print(f"[dim]Input tokens: {audit_decision.metadata['input_tokens']}[/dim]")
            console.print(f"[dim]Output tokens: {audit_decision.metadata['output_tokens']}[/dim]")
            console.print(f"[dim]Model: {audit_decision.metadata['model']}[/dim]")

        console.print("\n[green]✓ Receipt inspection complete![/green]")
        console.print(f"[yellow]→ Session ID: {receipt_id}[/yellow]")
        console.print("[yellow]→ View traces in Langfuse: http://localhost:3000[/yellow]\n")

        # Flush Langfuse to ensure all traces are sent
        from langfuse.decorators import langfuse_context
        langfuse_context.flush()

    except FileNotFoundError:
        console.print(f"[red]Error: Image file not found: {example_image_path}[/red]")
        console.print("[yellow]Note: This example requires actual receipt images.[/yellow]")
        console.print("[yellow]See data/datasets/receipt_test_cases.json for test case structure.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error processing receipt: {str(e)}[/red]")
        raise


if __name__ == "__main__":
    asyncio.run(main())
